from flask import Blueprint, request, jsonify
import os
from . import gemini_handler
from . import pollinations_text_handler
from . import pollinations_tts_handler
from .pollinations_tts_handler import CONTENT_POLICY_ERROR_SIGNAL
from .sentence_processor import split_text_into_sentence_chunks, process_sentence_level_media_generation
from .model_selector import get_available_models_for_provider
from .utils import get_media_path, generate_unique_filename, api_delay
from . import prompt_template_utils as ptu
from werkzeug.utils import secure_filename

enhanced_bp = Blueprint('enhanced', __name__, url_prefix='/enhanced')

@enhanced_bp.route('/process_with_sentence_level', methods=['POST'])
def process_with_sentence_level():
    """
    Endpoint baru untuk memproses narasi dengan logika level kalimat.
    """
    try:
        data = request.form
        files = request.files
        
        ai_provider = data.get('ai_provider', 'gemini')
        narrative_source = data.get('narrative_source', 'prompt')
        
        print(f"\n--- Enhanced Processing: {ai_provider} provider, {narrative_source} source ---")
        
        # Konfigurasi API berdasarkan provider
        if ai_provider == 'gemini':
            gemini_api_key = data.get('gemini_api_key', os.environ.get('GEMINI_API_KEY'))
            if not gemini_api_key:
                return jsonify({"error": "Gemini API Key dibutuhkan."}), 400
            if not gemini_handler.configure_gemini(gemini_api_key):
                return jsonify({"error": "Konfigurasi Gemini API Key gagal."}), 500
        
        # Ambil parameter yang diperlukan
        narrative_language = data.get('narrative_language', 'Indonesia (Default)')
        character_description = data.get('character_description', '')
        tts_tone = data.get('tts_tone', 'normal')
        tts_max_retries = int(data.get('tts_max_retries', 2))
        
        # Mapping bahasa untuk TTS
        LANG_MAP_TTS = {
            "Indonesia (Default)": "id-ID", "Inggris (English)": "en-US", 
            "Jerman (Deutsch)": "de-DE", "Spanyol (Español)": "es-ES", 
            "Prancis (Français)": "fr-FR", "Jepang (日本語)": "ja-JP",
            "Korea (한국어)": "ko-KR", "Arab (العربية)": "ar-SA", 
            "Mandarin (中文)": "zh-CN"
        }
        bahasa_code_for_tts = LANG_MAP_TTS.get(narrative_language, "id-ID")
        
        # Dapatkan teks narasi
        full_story_text = ""
        
        if narrative_source == 'file':
            print("Membaca narasi dari file yang diunggah...")
            if 'narrative_file' not in files or not files.getlist('narrative_file')[0].filename:
                return jsonify({"error": "Tidak ada file narasi yang dipilih."}), 400
            
            full_story_text_parts = []
            for uploaded_file in files.getlist('narrative_file'):
                if uploaded_file and uploaded_file.filename.endswith('.txt'):
                    try:
                        filename = secure_filename(uploaded_file.filename)
                        unique_filename_part = generate_unique_filename(prefix=os.path.splitext(filename)[0], extension="txt")
                        uploaded_filepath_part = get_media_path("uploaded_narratives", unique_filename_part)
                        uploaded_file.save(uploaded_filepath_part)
                        with open(uploaded_filepath_part, "r", encoding="utf-8") as f_part:
                            full_story_text_parts.append(f_part.read())
                    except Exception as e:
                        print(f"Error memproses file '{uploaded_file.filename}': {e}")
            
            if not full_story_text_parts:
                return jsonify({"error": "Tidak ada file narasi .txt yang valid."}), 400
            
            full_story_text = "\n\n".join(full_story_text_parts)
            
        elif narrative_source == 'prompt':
            print("Menggunakan narasi dari prompt yang sudah dihasilkan...")
            # Untuk sumber prompt, kita asumsikan teks sudah tersedia dari proses sebelumnya
            # atau kita perlu generate di sini
            story_prompt_input = data.get('story_prompt')
            if not story_prompt_input:
                return jsonify({"error": "Story prompt kosong."}), 400
            
            # Generate story menggunakan provider yang dipilih
            if ai_provider == 'gemini':
                selected_model = data.get('gemini_model', 'gemini-2.0-flash')
                prompt_template_id = data.get('prompt_template_id')
                
                if prompt_template_id:
                    selected_template = ptu.get_template_by_id(prompt_template_id)
                    if selected_template and selected_template.get('type') == 'story':
                        template_fill_data = {
                            "expertise": data.get('narrative_expertise', 'seorang pendongeng ulung'),
                            "language": narrative_language,
                            "tone": data.get('narrative_tone', 'normal'),
                            "format_style": data.get('narrative_format', 'narasi deskriptif'),
                            "target_words": "1000-1500",
                            "main_story_prompt": story_prompt_input,
                            "previous_summary_content": "",
                            "character_description_content": character_description
                        }
                        
                        full_story_text = gemini_handler.generate_story_part_from_template(
                            gemini_api_key=gemini_api_key,
                            model_name=selected_model,
                            template_content=selected_template['content'],
                            fill_data=template_fill_data,
                            part_number=1
                        )
            
            elif ai_provider == 'pollinations':
                selected_model = data.get('pollinations_text_model', 'openai')
                system_prompt = (f"Anda adalah {data.get('narrative_expertise', 'seorang pendongeng ulung')}. "
                               f"Tuliskan cerita dengan nada {data.get('narrative_tone', 'normal')} "
                               f"dalam bahasa {narrative_language}. Targetkan 1000-1500 kata.")
                
                full_story_text = pollinations_text_handler.generate_text_pollinations(
                    main_prompt=story_prompt_input,
                    model=selected_model,
                    system_prompt=system_prompt,
                    private=True
                )
        
        if not full_story_text or not full_story_text.strip():
            return jsonify({"error": "Gagal mendapatkan teks narasi."}), 500
        
        print(f"Teks narasi berhasil didapat: {len(full_story_text)} karakter")
        
        # LOGIKA BARU: Pecah teks menjadi paragraf dan kalimat
        print("\n--- Memecah teks menjadi paragraf dan kalimat ---")
        paragraph_chunks = split_text_into_sentence_chunks(full_story_text, max_chars_per_chunk=600)
        
        if not paragraph_chunks:
            return jsonify({"error": "Gagal memecah teks menjadi paragraf dan kalimat."}), 500
        
        print(f"Berhasil memecah menjadi {len(paragraph_chunks)} paragraf")
        for i, (para, sentences) in enumerate(paragraph_chunks):
            print(f"  Paragraf {i+1}: {len(sentences)} kalimat, {len(para)} karakter")
        
        # Proses setiap paragraf dan kalimat untuk generate prompts
        image_template_id = data.get('image_prompt_template_id')
        image_template = ptu.get_template_by_id(image_template_id) if image_template_id else None
        template_content = image_template['content'] if image_template else None
        
        processed_segments = process_sentence_level_media_generation(
            paragraph_chunks=paragraph_chunks,
            ai_provider=ai_provider,
            gemini_handler_module=gemini_handler,
            pollinations_text_handler_module=pollinations_text_handler,
            character_description=character_description,
            language="Inggris",  # Untuk prompt gambar selalu gunakan Inggris
            template_content=template_content
        )
        
        # Generate TTS untuk setiap paragraf (bukan per kalimat)
        print("\n--- Generating TTS untuk setiap paragraf ---")
        segments_with_audio = []
        successful_audio_count = 0
        failed_audio_count = 0
        
        for segment in processed_segments:
            paragraph_text = segment['paragraph_text']
            print(f"\nGenerating TTS untuk paragraf {segment['segment_index'] + 1}...")
            
            # Generate audio untuk seluruh paragraf
            audio_content = pollinations_tts_handler.generate_audio_from_text(
                text_input=paragraph_text,
                bahasa=bahasa_code_for_tts,
                nada=tts_tone,
                max_retries_override=tts_max_retries
            )
            
            # Handle content policy violations
            if audio_content == CONTENT_POLICY_ERROR_SIGNAL:
                print(f"  Paragraf {segment['segment_index'] + 1} terkena kebijakan konten TTS.")
                # Coba rewrite dengan Gemini jika tersedia
                if ai_provider == 'gemini' and gemini_handler:
                    rewritten_text = gemini_handler.rewrite_text_for_content_policy(
                        data.get('gemini_model', 'gemini-2.0-flash'),
                        paragraph_text,
                        language=narrative_language
                    )
                    if rewritten_text:
                        audio_content = pollinations_tts_handler.generate_audio_from_text(
                            text_input=rewritten_text,
                            bahasa=bahasa_code_for_tts,
                            nada=tts_tone,
                            max_retries_override=tts_max_retries
                        )
            
            # Simpan audio jika berhasil
            if audio_content and audio_content != CONTENT_POLICY_ERROR_SIGNAL:
                try:
                    audio_filename = generate_unique_filename(prefix="enhanced_tts", extension="mp3")
                    audio_file_path = get_media_path("audio", audio_filename)
                    with open(audio_file_path, 'wb') as f:
                        f.write(audio_content)
                    
                    segment['audio_path'] = audio_file_path
                    segments_with_audio.append(segment)
                    successful_audio_count += 1
                    print(f"  Audio berhasil disimpan: {audio_file_path}")
                except Exception as e:
                    print(f"  Error menyimpan audio: {e}")
                    failed_audio_count += 1
            else:
                print(f"  Gagal generate audio untuk paragraf {segment['segment_index'] + 1}")
                failed_audio_count += 1
            
            api_delay(10)  # Delay antar paragraf
        
        # Buat laporan
        report = {
            "total_paragraphs_processed": len(paragraph_chunks),
            "total_sentences_processed": sum(len(sentences) for _, sentences in paragraph_chunks),
            "total_image_prompts_generated": sum(len(seg['image_prompts']) for seg in processed_segments),
            "audio_generated_successfully": successful_audio_count,
            "audio_generation_failed": failed_audio_count,
            "segments_ready_for_video": len(segments_with_audio)
        }
        
        print("\n--- Laporan Enhanced Processing ---")
        for key, value in report.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if not segments_with_audio:
            return jsonify({
                "error": "Tidak ada segmen yang berhasil diproses dengan audio.",
                "report": report
            }), 500
        
        return jsonify({
            "message": "Enhanced processing berhasil dengan logika level kalimat.",
            "segments_to_process": segments_with_audio,
            "report": report,
            "full_story_preview": full_story_text[:1000] + ("..." if len(full_story_text) > 1000 else "")
        })
        
    except Exception as e:
        print(f"Error dalam enhanced processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500
