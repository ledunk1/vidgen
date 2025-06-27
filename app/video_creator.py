from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, ColorClip
import moviepy.video.fx.all as vfx 
import os
import random

from app.utils import generate_unique_filename, get_media_path, IMAGE_ASPECT_RATIOS_PIXELS, DEFAULT_IMAGE_ASPECT_RATIO_UI
from app.gpu_detector import gpu_detector

def apply_zoom_effect(clip, direction="in", zoom_magnitude=0.15):
    """Menerapkan efek zoom ke klip."""
    if direction == "out":
        # PERBAIKAN: Zoom out yang dimulai dari scale yang lebih besar untuk menghindari border
        # Mulai dari scale yang lebih besar, lalu zoom out ke scale normal
        start_zoom = 1.0 + (zoom_magnitude * 2.0)  # Mulai dari scale yang lebih besar
        end_zoom = 1.0  # Berakhir di scale normal
    else: # Zoom In
        start_zoom = 1.0  # Mulai dari scale normal
        end_zoom = 1.0 + zoom_magnitude  # Berakhir di scale yang lebih besar
    
    def resize_func(t):
        if clip.duration is None or clip.duration == 0: 
            return start_zoom
        progress = (t / clip.duration) * 0.5
        # progress = (t / clip.duration) * 0.5 untuk zoomout speed
        # Smooth interpolation dari start_zoom ke end_zoom
        return start_zoom + (end_zoom - start_zoom) * progress
    
    return clip.fx(vfx.resize, resize_func).set_position('center', 'center')

def create_placeholder_image_clip(duration, video_size, text="Audio Only"):
    """
    Membuat klip gambar placeholder untuk segmen yang hanya memiliki audio.
    """
    try:
        # Buat klip warna solid sebagai background
        placeholder_clip = ColorClip(size=video_size, color=(30, 30, 30), duration=duration)
        
        # Tambahkan teks jika diperlukan (opsional, bisa dikomentari jika tidak diinginkan)
        # from moviepy.editor import TextClip
        # text_clip = TextClip(text, fontsize=50, color='white', font='Arial').set_duration(duration)
        # text_clip = text_clip.set_position('center').set_duration(duration)
        # placeholder_clip = CompositeVideoClip([placeholder_clip, text_clip])
        
        return placeholder_clip
    except Exception as e:
        print(f"Error membuat placeholder clip: {e}")
        # Fallback: buat klip warna sederhana
        return ColorClip(size=video_size, color=(30, 30, 30), duration=duration)

def create_image_clip_with_effects(img_path, duration, video_size, effect_settings, effects_enabled):
    """
    Membuat klip gambar dengan efek yang diterapkan.
    Fungsi terpisah untuk reusability.
    """
    img_clip_original = None
    try:
        # Buat klip gambar dengan durasi yang ditentukan
        img_clip_original = ImageClip(img_path).set_duration(duration)
        
        # PERBAIKAN SCALING: Scaling yang disesuaikan untuk setiap efek
        img_w, img_h = img_clip_original.w, img_clip_original.h
        target_w, target_h = video_size
        
        print(f"    Gambar: {img_w}x{img_h}, Target: {target_w}x{target_h}")
        
        # Hitung rasio scaling untuk memastikan gambar mengisi frame penuh
        scale_w = target_w / img_w
        scale_h = target_h / img_h
        base_scale = max(scale_w, scale_h)  # Scale minimum untuk mengisi frame
        
        # Tentukan efek yang akan diterapkan terlebih dahulu
        chosen_effect = "static"
        if effects_enabled:
            motion_probs = {
                "zoom_in": effect_settings.get("zoom_in_prob", 40), 
                "zoom_out": effect_settings.get("zoom_out_prob", 20), 
                "static": effect_settings.get("static_prob", 40)
            }
            total_prob = sum(motion_probs.values())
            chosen_effect = random.choices(list(motion_probs.keys()), weights=list(motion_probs.values()), k=1)[0] if total_prob > 0 else "static"
        
        # PERBAIKAN UTAMA: Scale berbeda berdasarkan efek + margin untuk zoom out
        if chosen_effect == "zoom_out":
            # Untuk zoom out, gunakan scale yang jauh lebih besar agar ada ruang untuk zoom keluar
            final_scale = base_scale * 1.5  # Scale besar untuk zoom out
            print(f"    Zoom out detected - using scale: {final_scale:.2f}")
        else:
            # Untuk zoom in atau static, gunakan scale normal
            final_scale = base_scale * 1.2
            print(f"    Zoom in/static - using scale: {final_scale:.2f}")
        
        # LANGKAH 1: Resize gambar dengan scale yang sudah dihitung
        resized_clip = img_clip_original.fx(vfx.resize, final_scale)
        
        # LANGKAH 2: Terapkan efek zoom SEBELUM crop (ini yang penting!)
        processed_clip = resized_clip
        if effects_enabled:
            if chosen_effect == "zoom_in": 
                processed_clip = apply_zoom_effect(resized_clip, "in", zoom_magnitude=0.15)
                print(f"    Applied zoom in effect")
            elif chosen_effect == "zoom_out": 
                # PERBAIKAN KUNCI: Zoom out dengan magnitude yang lebih besar
                # Ini akan membuat gambar zoom dari scale besar ke scale normal
                processed_clip = apply_zoom_effect(resized_clip, "out", zoom_magnitude=0.25)
                print(f"    Applied zoom out effect")
            else:
                print(f"    Applied static effect")
        
        # LANGKAH 3: Crop ke ukuran target SETELAH efek diterapkan
        # Ini memastikan zoom out bisa "keluar" dari batas frame
        final_clip = processed_clip.fx(vfx.crop, 
                                       x_center=processed_clip.w / 2, 
                                       y_center=processed_clip.h / 2, 
                                       width=target_w, 
                                       height=target_h)
        
        # LANGKAH 4: Terapkan fade effect jika diperlukan
        if effects_enabled and random.random() < effect_settings.get("fade_prob", 0.5):
            fade_duration = min(0.5, duration * 0.2)
            final_clip = final_clip.fadein(fade_duration).fadeout(fade_duration)
            print(f"    Applied fade effect")

        return final_clip, chosen_effect
        
    except Exception as e:
        print(f"    Error memproses gambar {img_path}: {e}")
        if img_clip_original:
            try:
                img_clip_original.close()
            except:
                pass
        return None, None

def get_video_codec_settings(gpu_acceleration_enabled=True):
    """
    Mendapatkan pengaturan codec video berdasarkan GPU acceleration setting
    """
    if gpu_acceleration_enabled and gpu_detector.gpu_acceleration_available:
        # Gunakan hardware encoder terbaik yang tersedia
        encoder = gpu_detector.get_best_encoder(prefer_hardware=True)
        decoder = gpu_detector.get_best_decoder(prefer_hardware=True)
        
        # Log status GPU
        gpu_detector.log_gpu_status(gpu_acceleration_enabled=True)
        
        # Pengaturan khusus untuk setiap encoder
        if encoder == 'h264_qsv':
            return {
                'codec': 'h264_qsv',
                'ffmpeg_params': ['-preset', 'fast', '-global_quality', '23'],
                'decoder': decoder
            }
        elif encoder == 'h264_nvenc':
            return {
                'codec': 'h264_nvenc',
                'ffmpeg_params': ['-preset', 'fast', '-cq', '23'],
                'decoder': decoder
            }
        elif encoder == 'h264_amf':
            return {
                'codec': 'h264_amf',
                'ffmpeg_params': ['-quality', 'speed', '-rc', 'cqp', '-qp_i', '23'],
                'decoder': decoder
            }
        else:
            # Fallback ke CPU
            gpu_detector.log_gpu_status(gpu_acceleration_enabled=False)
            return {
                'codec': 'libx264',
                'ffmpeg_params': ['-preset', 'fast', '-crf', '23'],
                'decoder': None
            }
    else:
        # GPU acceleration disabled atau tidak tersedia
        gpu_detector.log_gpu_status(gpu_acceleration_enabled=False)
        return {
            'codec': 'libx264',
            'ffmpeg_params': ['-preset', 'fast', '-crf', '23'],
            'decoder': None
        }

def create_video_from_parts(
    story_segments_data, 
    aspect_ratio_str=DEFAULT_IMAGE_ASPECT_RATIO_UI,
    effect_settings=None, 
    output_video_name_prefix="final_story_video",
    gpu_acceleration_enabled=True
    ):
    # --- LOGIKA BARU: Daftar untuk menyimpan klip video mini yang sudah sinkron ---
    video_clips_for_final_concatenation = []
    all_source_clips_to_close = []
    
    # TAMBAHAN BARU: Menyimpan gambar dari segmen sebelumnya untuk reuse
    previous_segment_images = []

    print("\n--- MEMULAI PEMBUATAN VIDEO (Logika Sinkronisasi per Segmen dengan Reuse Gambar Sebelumnya) ---")

    current_video_w, current_video_h = IMAGE_ASPECT_RATIOS_PIXELS.get(aspect_ratio_str, IMAGE_ASPECT_RATIOS_PIXELS[DEFAULT_IMAGE_ASPECT_RATIO_UI])
    current_video_size = (current_video_w, current_video_h)
    print(f"Menggunakan resolusi video: {current_video_size} untuk aspek rasio {aspect_ratio_str}")
    
    # Dapatkan pengaturan codec berdasarkan GPU acceleration setting
    codec_settings = get_video_codec_settings(gpu_acceleration_enabled)
    
    if effect_settings is None: 
        effect_settings = {"enabled": True, "fade_prob": 0.5, "zoom_in_prob": 40, "zoom_out_prob": 20, "static_prob": 40}
    
    effects_are_generally_enabled = effect_settings.get("enabled", False)
    if effects_are_generally_enabled: print("Efek visual diaktifkan dengan pengaturan:", effect_settings)
    else: print("Semua efek visual dinonaktifkan.")

    # --- PERUBAHAN UTAMA: Membuat klip mini untuk setiap segmen dengan fallback ke gambar sebelumnya ---
    for i, segment_data in enumerate(story_segments_data):
        print(f"\nMemproses segmen video ke-{i+1}...")
        audio_path = segment_data.get('audio_path')
        image_paths = segment_data.get('image_paths', [])
        
        # PERUBAHAN: Hanya memerlukan audio, gambar opsional
        if not (audio_path and os.path.exists(audio_path)):
            print(f"  Peringatan: Audio tidak tersedia untuk segmen {i+1}. Melewati."); continue

        audio_clip_for_segment = None
        try:
            # 1. Muat audio untuk segmen ini dan dapatkan durasinya.
            audio_clip_for_segment = AudioFileClip(audio_path)
            all_source_clips_to_close.append(audio_clip_for_segment)
            segment_duration = audio_clip_for_segment.duration
            
            if segment_duration is None or segment_duration <= 0:
                print(f"  Peringatan: Durasi audio tidak valid untuk segmen {i+1}. Melewati."); continue
            
            segment_image_clips = []
            
            # PERUBAHAN UTAMA: Cek apakah ada gambar yang valid
            valid_image_paths = [path for path in image_paths if os.path.exists(path)]
            
            if valid_image_paths:
                # 2a. Ada gambar: Bagi durasi audio segmen secara merata ke semua gambar DALAM segmen ini.
                duration_per_image = segment_duration / len(valid_image_paths)
                print(f"  Segmen {i+1}: Durasi audio={segment_duration:.2f}s, Gambar={len(valid_image_paths)}, Durasi/gambar={duration_per_image:.2f}s")

                for img_path in valid_image_paths:
                    final_clip, chosen_effect = create_image_clip_with_effects(
                        img_path, duration_per_image, current_video_size, 
                        effect_settings, effects_are_generally_enabled
                    )
                    
                    if final_clip:
                        segment_image_clips.append(final_clip)
                        print(f"    Klip gambar berhasil diproses dengan efek: {chosen_effect}")
                
                # Simpan gambar segmen ini untuk segmen berikutnya yang mungkin tidak punya gambar
                previous_segment_images = valid_image_paths.copy()
                print(f"  Menyimpan {len(previous_segment_images)} gambar untuk segmen berikutnya")
                
            elif previous_segment_images:
                # 2b. TIDAK ada gambar TAPI ada gambar dari segmen sebelumnya: Gunakan gambar sebelumnya
                print(f"  Segmen {i+1}: Tidak ada gambar, menggunakan {len(previous_segment_images)} gambar dari segmen sebelumnya")
                
                # Bagi durasi audio dengan gambar dari segmen sebelumnya
                duration_per_image = segment_duration / len(previous_segment_images)
                print(f"  Durasi audio={segment_duration:.2f}s, Gambar reuse={len(previous_segment_images)}, Durasi/gambar={duration_per_image:.2f}s")
                
                for img_path in previous_segment_images:
                    if os.path.exists(img_path):  # Pastikan gambar masih ada
                        final_clip, chosen_effect = create_image_clip_with_effects(
                            img_path, duration_per_image, current_video_size, 
                            effect_settings, effects_are_generally_enabled
                        )
                        
                        if final_clip:
                            segment_image_clips.append(final_clip)
                            print(f"    Klip gambar reuse berhasil diproses dengan efek: {chosen_effect}")
                    else:
                        print(f"    Peringatan: Gambar reuse tidak ditemukan: {img_path}")
                
                # Jangan update previous_segment_images karena kita menggunakan yang lama
                print(f"  Tetap menggunakan gambar yang sama untuk segmen berikutnya")
                
            else:
                # 2c. TIDAK ada gambar dan TIDAK ada gambar sebelumnya: Buat placeholder visual
                print(f"  Segmen {i+1}: Tidak ada gambar dan tidak ada gambar sebelumnya, membuat placeholder visual untuk durasi {segment_duration:.2f}s")
                try:
                    placeholder_clip = create_placeholder_image_clip(segment_duration, current_video_size, f"Audio Segment {i+1}")
                    segment_image_clips.append(placeholder_clip)
                    print(f"    Placeholder visual berhasil dibuat")
                except Exception as e_placeholder:
                    print(f"  Error membuat placeholder visual: {e_placeholder}. Melewati segmen.")
                    continue
            
            if not segment_image_clips:
                print(f"  Peringatan: Tidak ada klip visual valid untuk segmen {i+1}."); continue

            # 4. Gabungkan SEMUA klip visual untuk segmen ini menjadi satu klip visual.
            if len(segment_image_clips) == 1:
                segment_visual_clip = segment_image_clips[0]
            else:
                segment_visual_clip = concatenate_videoclips(segment_image_clips, method="compose")
            
            # 5. Pasangkan klip visual segmen dengan audio segmen untuk membuat "klip video mini" yang sinkron.
            segment_video_with_audio = segment_visual_clip.set_audio(audio_clip_for_segment)
            
            # 6. Tambahkan klip mini yang sudah jadi ini ke daftar utama.
            video_clips_for_final_concatenation.append(segment_video_with_audio)
            print(f"  Segmen video ke-{i+1} berhasil dibuat dan disinkronkan.")

        except Exception as e_seg:
            print(f"  Error besar saat memproses segmen {i+1}: {e_seg}")
            if audio_clip_for_segment: 
                try:
                    audio_clip_for_segment.close()
                except:
                    pass

    if not video_clips_for_final_concatenation: 
        print("Tidak ada segmen video yang valid untuk digabungkan."); return None

    final_video_obj = None
    try:
        # 7. Gabungkan semua "klip video mini" yang sudah sinkron menjadi satu video akhir.
        print(f"\nFINALE: Menggabungkan {len(video_clips_for_final_concatenation)} segmen video...")
        final_video_obj = concatenate_videoclips(video_clips_for_final_concatenation, method="compose")
        if not final_video_obj: raise ValueError("Gagal menggabungkan klip video akhir.")
            
        output_filename = generate_unique_filename(prefix=output_video_name_prefix, extension="mp4")
        output_filepath = get_media_path("videos", output_filename) 
        
        print(f"Menulis video akhir ke: {output_filepath}...")
        print(f"Menggunakan codec: {codec_settings['codec']}")
        
        # Siapkan parameter FFmpeg
        ffmpeg_params = codec_settings['ffmpeg_params'].copy()
        
        # Tambahkan decoder jika tersedia
        if codec_settings['decoder']:
            print(f"Menggunakan hardware decoder: {codec_settings['decoder']}")
            # Note: MoviePy tidak secara langsung mendukung hardware decoder
            # Ini lebih untuk informasi dan bisa diimplementasikan di masa depan
        
        final_video_obj.write_videofile(
            output_filepath, 
            fps=24, 
            codec=codec_settings['codec'], 
            audio_codec='aac', 
            threads=os.cpu_count() or 4, 
            ffmpeg_params=ffmpeg_params,
            logger='bar',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        print("Video akhir berhasil dibuat.")
        return output_filepath
    except Exception as e_final:
        print(f"Error saat menulis video akhir: {e_final}")
        # Jika hardware encoder gagal, coba fallback ke CPU
        if gpu_acceleration_enabled and codec_settings['codec'] != 'libx264':
            print("Hardware encoder gagal, mencoba fallback ke CPU encoder...")
            try:
                final_video_obj.write_videofile(
                    output_filepath, 
                    fps=24, 
                    codec='libx264', 
                    audio_codec='aac', 
                    threads=os.cpu_count() or 4, 
                    preset='fast',
                    logger='bar',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True
                )
                print("Video akhir berhasil dibuat dengan CPU encoder.")
                return output_filepath
            except Exception as e_fallback:
                print(f"CPU encoder juga gagal: {e_fallback}")
        
        import traceback
        traceback.print_exc()
        return None
    finally:
        print("Membersihkan klip MoviePy...")
        if final_video_obj: 
            try:
                final_video_obj.close()
            except:
                pass
        # Klip di dalam `video_clips_for_final_concatenation` akan ditutup oleh `final_video_obj.close()`
        # Kita hanya perlu menutup klip sumber asli
        for clip in all_source_clips_to_close:
            try: 
                clip.close()
            except Exception: 
                pass
        print("Pembersihan selesai.")