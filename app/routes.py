from flask import Blueprint, render_template, request, jsonify, current_app, url_for
import os
import random
import uuid 
import json 
import base64 
from werkzeug.utils import secure_filename

from . import gemini_handler
# Menggunakan nama fungsi yang sudah diperbarui dan konstanta error
from . import pollinations_tts_handler 
from .pollinations_tts_handler import CONTENT_POLICY_ERROR_SIGNAL 
from . import pollinations_image_handler 
from . import pollinations_text_handler 
from . import video_creator
from .utils import (
    split_text_into_chunks, api_delay, get_media_path, generate_unique_filename, 
    AVAILABLE_GEMINI_MODELS, DEFAULT_GEMINI_MODEL,
    POLLINATIONS_TEXT_MODELS, DEFAULT_POLLINATIONS_TEXT_MODEL, 
    PUTER_AI_CHAT_MODELS, DEFAULT_PUTER_AI_CHAT_MODEL, 
    POLLINATIONS_VOICES, DEFAULT_POLLINATIONS_VOICE, 
    POLLINATIONS_VOICE_STYLES, DEFAULT_POLLINATIONS_VOICE_STYLE,
    POLLINATIONS_IMAGE_MODELS, DEFAULT_POLLINATIONS_IMAGE_MODEL, 
    ALL_IMAGE_ASPECT_RATIOS, DEFAULT_IMAGE_ASPECT_RATIO_UI,
    WORDS_PER_STORY_PART as DEFAULT_WORDS_PER_PART, 
    IMAGES_PER_PARAGRAPH_MIN, 
    IMAGES_PER_PARAGRAPH_MAX, 
    NARRATIVE_EXPERTISE_OPTIONS, DEFAULT_NARRATIVE_EXPERTISE,
    NARRATIVE_TONE_OPTIONS, DEFAULT_NARRATIVE_TONE,
    NARRATIVE_FORMAT_OPTIONS, DEFAULT_NARRATIVE_FORMAT,
    NARRATIVE_LANGUAGE_OPTIONS, DEFAULT_NARRATIVE_LANGUAGE,
    DEFAULT_EFFECTS_ENABLED, 
    DEFAULT_FADE_PROBABILITY,
    DEFAULT_ZOOM_IN_PROBABILITY, DEFAULT_ZOOM_OUT_PROBABILITY,
    DEFAULT_STATIC_PROBABILITY,
    DEFAULT_TTS_MAX_RETRIES,
    DEFAULT_IMAGE_MAX_RETRIES,
    DEFAULT_GPU_ACCELERATION_ENABLED
)
from . import prompt_template_utils as ptu
# Import enhanced processing modules
from .sentence_processor import split_text_into_sentence_chunks, process_sentence_level_media_generation
from .model_selector import get_available_models_for_provider, should_show_model_selection

bp = Blueprint('main', __name__)

CHUNK_TEXT_DIR = "story_chunks" 
FULL_STORY_DIR = "full_stories" 
UPLOADED_NARRATIVES_DIR = "uploaded_narratives"

def ensure_media_dirs():
    if current_app:
        base_static_path = current_app.static_folder
        generated_media_base = os.path.join(base_static_path, "generated_media")
        os.makedirs(generated_media_base, exist_ok=True)
        for media_type in ["audio", "images", "videos", CHUNK_TEXT_DIR, FULL_STORY_DIR, UPLOADED_NARRATIVES_DIR]:
            path_to_create = get_media_path(media_type, '', base_dir_name="generated_media")
            os.makedirs(path_to_create, exist_ok=True)
        ptu.get_templates_filepath() 
    else:
        print("Peringatan: current_app tidak tersedia saat ensure_media_dirs dipanggil.")

@bp.route('/', methods=['GET'])
def index():
    all_templates = ptu.load_prompt_templates()
    
    print(f"DEBUG ROUTES.PY (index): Tipe PUTER_AI_CHAT_MODELS: {type(PUTER_AI_CHAT_MODELS)}")
    if PUTER_AI_CHAT_MODELS:
        print(f"DEBUG ROUTES.PY (index): Panjang PUTER_AI_CHAT_MODELS: {len(PUTER_AI_CHAT_MODELS)}")

    return render_template(
        'index.html',
        gemini_models=AVAILABLE_GEMINI_MODELS, default_gemini_model=DEFAULT_GEMINI_MODEL,
        pollinations_text_models=POLLINATIONS_TEXT_MODELS, default_pollinations_text_model=DEFAULT_POLLINATIONS_TEXT_MODEL,
        puter_ai_chat_models=PUTER_AI_CHAT_MODELS,
        default_puter_ai_chat_model=DEFAULT_PUTER_AI_CHAT_MODEL,
        pollinations_voices=POLLINATIONS_VOICES, default_voice=DEFAULT_POLLINATIONS_VOICE,
        pollinations_voice_styles=POLLINATIONS_VOICE_STYLES, default_voice_style=DEFAULT_POLLINATIONS_VOICE_STYLE,
        pollinations_image_models=POLLINATIONS_IMAGE_MODELS, default_pollinations_image_model=DEFAULT_POLLINATIONS_IMAGE_MODEL,
        image_aspect_ratios=ALL_IMAGE_ASPECT_RATIOS, default_image_aspect_ratio=DEFAULT_IMAGE_ASPECT_RATIO_UI,
        default_parts=1, words_per_story_part=DEFAULT_WORDS_PER_PART, 
        images_per_paragraph_min=IMAGES_PER_PARAGRAPH_MIN, images_per_paragraph_max=IMAGES_PER_PARAGRAPH_MAX, 
        narrative_expertise_options=NARRATIVE_EXPERTISE_OPTIONS, default_narrative_expertise=DEFAULT_NARRATIVE_EXPERTISE,
        narrative_tone_options=NARRATIVE_TONE_OPTIONS, default_narrative_tone=DEFAULT_NARRATIVE_TONE,
        narrative_format_options=NARRATIVE_FORMAT_OPTIONS, default_narrative_format=DEFAULT_NARRATIVE_FORMAT,
        narrative_language_options=NARRATIVE_LANGUAGE_OPTIONS, default_narrative_language=DEFAULT_NARRATIVE_LANGUAGE,
        prompt_templates=all_templates,
        default_effects_enabled=DEFAULT_EFFECTS_ENABLED,
        default_fade_probability=DEFAULT_FADE_PROBABILITY,
        default_zoom_in_probability=DEFAULT_ZOOM_IN_PROBABILITY, 
        default_zoom_out_probability=DEFAULT_ZOOM_OUT_PROBABILITY,
        default_static_probability=DEFAULT_STATIC_PROBABILITY,
        default_tts_max_retries=DEFAULT_TTS_MAX_RETRIES,
        default_image_max_retries=DEFAULT_IMAGE_MAX_RETRIES,
        default_gpu_acceleration_enabled=DEFAULT_GPU_ACCELERATION_ENABLED
    )

def rewrite_text_for_content_policy_with_provider(ai_provider, original_text, narrative_language, data):
    """
    PERBAIKAN: Fungsi untuk menulis ulang teks menggunakan provider AI yang dipilih user
    dengan fokus khusus untuk menghindari kebijakan konten TTS
    """
    rewritten_text = None
    
    # PERBAIKAN: Prompt yang lebih spesifik untuk TTS content policy
    tts_safe_instruction = (
        "Tulis ulang teks berikut agar SANGAT AMAN untuk text-to-speech dan mematuhi semua kebijakan konten. "
        "Hindari kata-kata yang berhubungan dengan: kekerasan, horor, supernatural, kematian, darah, hantu, "
        "setan, kutukan, penderitaan, atau hal-hal yang menakutkan. "
        "Ganti dengan kata-kata yang lebih netral dan aman. "
        "Pertahankan alur cerita dan makna inti, tapi buat versi yang sangat ramah untuk semua umur. "
        f"Teks harus dalam bahasa {narrative_language}. "
        "Hanya berikan teks hasil penulisan ulang tanpa tambahan komentar."
    )
    
    if ai_provider == 'gemini':
        gemini_api_key = data.get('gemini_api_key', os.environ.get('GEMINI_API_KEY'))
        if gemini_api_key and gemini_handler.configure_gemini(gemini_api_key):
            selected_model = data.get('gemini_model', DEFAULT_GEMINI_MODEL)
            
            # Gunakan prompt khusus untuk TTS safety
            safe_prompt = f"{tts_safe_instruction}\n\nTeks asli:\n{original_text}"
            
            rewritten_text = gemini_handler.generate_text_content(
                selected_model, safe_prompt, temperature=0.3, max_output_tokens=1024
            )
        else:
            print("  Peringatan: Gemini API Key tidak tersedia untuk rewrite teks.")
    
    elif ai_provider == 'pollinations':
        selected_model = data.get('pollinations_text_model', DEFAULT_POLLINATIONS_TEXT_MODEL)
        
        main_prompt = f"Teks yang perlu ditulis ulang untuk TTS: {original_text}"
        
        rewritten_text = pollinations_text_handler.generate_text_pollinations(
            main_prompt=main_prompt,
            model=selected_model,
            system_prompt=tts_safe_instruction,
            private=True,
            temperature=0.3
        )
        
        if rewritten_text and isinstance(rewritten_text, str):
            print("  Teks berhasil ditulis ulang oleh Pollinations untuk TTS safety.")
        else:
            print("  Gagal mendapatkan hasil penulisan ulang dari Pollinations.")
            rewritten_text = None
    
    else:
        print(f"  Provider AI '{ai_provider}' tidak mendukung rewrite teks untuk kebijakan konten.")
    
    return rewritten_text

@bp.route('/generate_media_prompts', methods=['POST'])
def generate_media_prompts_route():
    try:
        data = request.form
        files = request.files
        
        ai_provider = data.get('ai_provider', 'gemini') 
        narrative_source = data.get('narrative_source', 'prompt')
        use_enhanced_processing = data.get('use_enhanced_processing') == 'true'

        print(f"\n--- Konfigurasi Utama ---")
        print(f"Penyedia AI Narasi: {ai_provider}, Sumber Narasi: {narrative_source}")
        print(f"Enhanced Processing: {use_enhanced_processing}")

        # Enhanced Processing Logic
        if use_enhanced_processing:
            print("Menggunakan Enhanced Processing dengan logika level kalimat...")
            return handle_enhanced_processing(data, files, ai_provider, narrative_source)

        # Original processing logic (unchanged)
        gemini_api_key = None
        if ai_provider == 'gemini':
            gemini_api_key = data.get('gemini_api_key', os.environ.get('GEMINI_API_KEY'))
            if not gemini_api_key: 
                return jsonify({"error": "Gemini API Key dibutuhkan jika memilih Gemini sebagai penyedia narasi."}), 400
            if not gemini_handler.configure_gemini(gemini_api_key): 
                return jsonify({"error": "Konfigurasi Gemini API Key gagal."}), 500
        
        # --- Pengambilan Parameter TTS dengan Voice dan Style ---
        narrative_language = data.get('narrative_language', DEFAULT_NARRATIVE_LANGUAGE)
        tts_voice = data.get('tts_voice', DEFAULT_POLLINATIONS_VOICE)
        tts_voice_style = data.get('tts_voice_style', DEFAULT_POLLINATIONS_VOICE_STYLE)
        tts_max_retries = int(data.get('tts_max_retries', DEFAULT_TTS_MAX_RETRIES))
        
        # PERBAIKAN: Gunakan voice style yang lebih aman untuk konten yang mungkin sensitif
        safe_voice_styles = ["friendly", "calm", "patient_teacher", "mellow_story"]
        if tts_voice_style in ["horror_story", "noir_detective"]:
            print(f"PERINGATAN: Voice style '{tts_voice_style}' berisiko untuk konten sensitif. Akan menggunakan fallback jika diperlukan.")
        
        LANG_MAP_TTS = {
            "Indonesia (Default)": "id-ID", "Inggris (English)": "en-US", "Jerman (Deutsch)": "de-DE",
            "Spanyol (Español)": "es-ES", "Prancis (Français)": "fr-FR", "Jepang (日本語)": "ja-JP",
            "Korea (한국어)": "ko-KR", "Arab (العربية)": "ar-SA", "Mandarin (中文)": "zh-CN"
        }
        bahasa_code_for_tts = LANG_MAP_TTS.get(narrative_language, "id-ID")

        images_per_chunk_min_input = int(data.get('images_per_chunk_min', IMAGES_PER_PARAGRAPH_MIN))
        images_per_chunk_max_input = int(data.get('images_per_chunk_max', IMAGES_PER_PARAGRAPH_MAX))
        character_description = data.get('character_description', None)
        
        full_story_text = ""
        client_generated_image_prompts_parsed = None

        if ai_provider == 'puter_ai_chat':
            if narrative_source != 'prompt':
                return jsonify({"error": "Puter AI Chat hanya mendukung sumber narasi dari prompt."}), 400
            
            full_story_text = data.get('client_generated_story')
            client_generated_image_prompts_json = data.get('client_generated_image_prompts')

            if not full_story_text: return jsonify({"error": "Narasi dari klien (Puter AI) tidak diterima."}), 400
            if not client_generated_image_prompts_json: return jsonify({"error": "Prompt gambar dari klien (Puter AI) tidak diterima."}), 400
            try: client_generated_image_prompts_parsed = json.loads(client_generated_image_prompts_json)
            except json.JSONDecodeError: return jsonify({"error": "Format prompt gambar dari klien (Puter AI) tidak valid."}), 400
            print(f"Puter AI Flow: Narasi dan {len(client_generated_image_prompts_parsed)} set prompt gambar diterima dari klien.")

        elif narrative_source == 'file':
            print("\n--- TAHAP 1: MEMBACA NARASI DARI FILE UNGGAPAN (Untuk Gemini/Pollinations) ---")
            if 'narrative_file' not in files or not files.getlist('narrative_file')[0].filename : return jsonify({"error": "Tidak ada file narasi yang dipilih untuk diunggah."}), 400
            full_story_text_parts = []
            for uploaded_file in files.getlist('narrative_file'): 
                if uploaded_file and uploaded_file.filename.endswith('.txt'):
                    try:
                        filename = secure_filename(uploaded_file.filename)
                        unique_filename_part = generate_unique_filename(prefix=os.path.splitext(filename)[0], extension="txt")
                        uploaded_filepath_part = get_media_path(UPLOADED_NARRATIVES_DIR, unique_filename_part)
                        uploaded_file.save(uploaded_filepath_part)
                        with open(uploaded_filepath_part, "r", encoding="utf-8") as f_part: full_story_text_parts.append(f_part.read())
                    except Exception as e: print(f"Error memproses file unggahan '{uploaded_file.filename}': {e}")
                elif uploaded_file and uploaded_file.filename: print(f"Mengabaikan file '{uploaded_file.filename}' karena bukan .txt.")
            if not full_story_text_parts: return jsonify({"error": "Tidak ada file narasi .txt yang valid berhasil diproses."}), 400
            full_story_text = "\n\n".join(full_story_text_parts) 
            if not full_story_text.strip(): return jsonify({"error": "Konten gabungan dari file narasi yang diunggah kosong."}), 400
            print(f"Narasi dari file: {len(full_story_text)} karakter.")

        elif narrative_source == 'prompt':
            print("\n--- TAHAP 1: GENERASI NARASI DARI PROMPT (SERVER-SIDE untuk Gemini/Pollinations) ---")
            # PERBAIKAN: Ambil model yang dipilih berdasarkan provider
            selected_gemini_model_for_text = data.get('gemini_model', DEFAULT_GEMINI_MODEL) 
            selected_pollinations_text_model = data.get('pollinations_text_model', DEFAULT_POLLINATIONS_TEXT_MODEL)
            
            # Debug log untuk memastikan model terambil
            print(f"DEBUG: Selected Gemini Model: {selected_gemini_model_for_text}")
            print(f"DEBUG: Selected Pollinations Model: {selected_pollinations_text_model}")
            
            story_prompt_input = data.get('story_prompt')
            if not story_prompt_input: return jsonify({"error": "Story prompt kosong."}), 400
            num_parts = int(data.get('num_parts', 1))
            min_words_per_part = int(data.get('min_words_per_part', 100))
            max_words_per_part = int(data.get('max_words_per_part', 150))
            all_story_parts_text = []
            previous_summary = None
            for i in range(1, num_parts + 1):
                print(f"Memproses bagian cerita ke-{i} dari {num_parts} (server) menggunakan {ai_provider}...")
                current_part_text = None
                if ai_provider == 'gemini':
                    narrative_expertise = data.get('narrative_expertise', NARRATIVE_EXPERTISE_OPTIONS[DEFAULT_NARRATIVE_EXPERTISE])
                    narrative_tone = data.get('narrative_tone', NARRATIVE_TONE_OPTIONS[DEFAULT_NARRATIVE_TONE])
                    narrative_format = data.get('narrative_format', NARRATIVE_FORMAT_OPTIONS[DEFAULT_NARRATIVE_FORMAT])
                    prompt_template_id_story = data.get('prompt_template_id') 
                    if not prompt_template_id_story: return jsonify({"error": "Template prompt cerita harus dipilih untuk Gemini."}), 400
                    selected_story_template = ptu.get_template_by_id(prompt_template_id_story)
                    if not selected_story_template or selected_story_template.get('type') != 'story': return jsonify({"error": f"Template ID '{prompt_template_id_story}' tidak valid untuk cerita."}), 404
                    template_fill_data = {
                        "expertise": narrative_expertise, "language": narrative_language, "tone": narrative_tone,
                        "format_style": narrative_format, "target_words": f"{min_words_per_part}-{max_words_per_part}",
                        "main_story_prompt": story_prompt_input, "previous_summary_content": previous_summary if previous_summary else "", 
                        "character_description_content": character_description if character_description else ""
                    }
                    current_part_text = gemini_handler.generate_story_part_from_template(
                        gemini_api_key=gemini_api_key, model_name=selected_gemini_model_for_text, 
                        template_content=selected_story_template['content'], fill_data=template_fill_data, part_number=i
                    )
                elif ai_provider == 'pollinations':
                    system_prompt_pollinations = (f"Anda adalah {data.get('narrative_expertise', NARRATIVE_EXPERTISE_OPTIONS[DEFAULT_NARRATIVE_EXPERTISE])}. "
                        f"Tuliskan cerita dengan nada {data.get('narrative_tone', NARRATIVE_TONE_OPTIONS[DEFAULT_NARRATIVE_TONE])} "
                        f"dalam format {data.get('narrative_format', NARRATIVE_FORMAT_OPTIONS[DEFAULT_NARRATIVE_FORMAT])}. "
                        f"Cerita harus dalam bahasa {narrative_language}. Targetkan {min_words_per_part}-{max_words_per_part} kata.")
                    if previous_summary: system_prompt_pollinations += f"\nRingkasan sebelumnya: {previous_summary}"
                    current_part_text = pollinations_text_handler.generate_text_pollinations(
                        main_prompt=story_prompt_input, model=selected_pollinations_text_model,
                        system_prompt=system_prompt_pollinations, private=True
                    )
                if not current_part_text or "Error:" in current_part_text: return jsonify({"error": f"Gagal menghasilkan bagian cerita ke-{i} dengan {ai_provider}."}), 500
                all_story_parts_text.append(current_part_text)
                if i < num_parts: 
                    if ai_provider == 'gemini': previous_summary = gemini_handler.summarize_text(selected_gemini_model_for_text, current_part_text, language=narrative_language)
                    elif ai_provider == 'pollinations': previous_summary = pollinations_text_handler.summarize_text_pollinations(current_part_text, model=selected_pollinations_text_model, language=narrative_language)
                    if not previous_summary or "Error:" in previous_summary: previous_summary = current_part_text[-500:]
            full_story_text = "\n\n".join(all_story_parts_text)
            if not full_story_text.strip(): return jsonify({"error": "Gagal menghasilkan konten cerita (server-side)."}), 500
        else:
            return jsonify({"error": "Kombinasi Penyedia AI dan Sumber Narasi tidak valid."}), 400

        print("\n--- TAHAP 2: MEMECAH NARASI, TTS, & PROMPT GAMBAR ---")
        text_chunks = split_text_into_chunks(full_story_text, max_chars=600)
        if not text_chunks: return jsonify({"error": "Gagal memecah narasi."}), 500
        
        segments_for_client_generation = []
        successful_audio_count = 0; failed_audio_count = 0; rewritten_text_count = 0
        successful_prompt_sets_count = 0; failed_prompt_sets_count = 0
        total_individual_prompts_generated = 0; total_individual_prompts_attempted = 0
        previous_chunk_for_context = None 

        for idx, original_chunk_text_content in enumerate(text_chunks):
            print(f"\nMemproses chunk ke-{idx + 1}/{len(text_chunks)} untuk audio dan prompt gambar.")
            if not original_chunk_text_content.strip(): 
                print(f"  Chunk ke-{idx + 1} kosong, melewati."); continue
            
            current_segment_data_for_client = {
                'segment_index': idx, 'chunk_text': original_chunk_text_content, 
                'audio_path': None, 'image_prompts': [], 'num_images_target': 0 
            }
            
            # === PERBAIKAN UTAMA: PANGGILAN TTS DENGAN VOICE DAN STYLE ===
            audio_content = pollinations_tts_handler.generate_audio_from_text(
                text_input=original_chunk_text_content,
                bahasa=bahasa_code_for_tts,
                voice=tts_voice,
                voice_style=tts_voice_style,
                max_retries_override=tts_max_retries
            )
            
            # PERBAIKAN UTAMA: Cek hasil dari fungsi TTS dan gunakan provider yang benar untuk rewrite
            if audio_content == CONTENT_POLICY_ERROR_SIGNAL:
                print(f"  Chunk {idx+1} terkena kebijakan konten TTS.")
                
                # PERBAIKAN: Gunakan provider AI yang dipilih user untuk rewrite dengan fokus TTS safety
                rewritten_chunk_text = rewrite_text_for_content_policy_with_provider(
                    ai_provider, original_chunk_text_content, narrative_language, data
                )

                if rewritten_chunk_text:
                    rewritten_text_count += 1
                    print(f"  Chunk {idx+1} berhasil ditulis ulang dengan {ai_provider}. Mencoba TTS lagi.")
                    
                    # PERBAIKAN: Coba dengan voice style yang lebih aman untuk teks yang sudah ditulis ulang
                    safe_voice_style = "friendly" if tts_voice_style in ["horror_story", "noir_detective"] else tts_voice_style
                    
                    audio_content = pollinations_tts_handler.generate_audio_from_text(
                        text_input=rewritten_chunk_text,
                        bahasa=bahasa_code_for_tts,
                        voice=tts_voice,
                        voice_style=safe_voice_style,
                        max_retries_override=tts_max_retries
                    )
                    
                    # Update chunk text dengan yang sudah ditulis ulang untuk konsistensi
                    if audio_content and audio_content != CONTENT_POLICY_ERROR_SIGNAL:
                        current_segment_data_for_client['chunk_text'] = rewritten_chunk_text
                else: 
                    print(f"  Gagal menulis ulang teks dengan {ai_provider}.")
                    audio_content = None

            # Simpan file audio jika kontennya valid (bukan sinyal error atau None)
            audio_file_path = None
            if audio_content and audio_content != CONTENT_POLICY_ERROR_SIGNAL:
                try:
                    audio_filename = generate_unique_filename(prefix="tts_audio", extension="mp3")
                    audio_file_path = get_media_path("audio", audio_filename)
                    with open(audio_file_path, 'wb') as f:
                        f.write(audio_content)
                    print(f"  Audio untuk chunk {idx+1} berhasil disimpan di: {audio_file_path}")
                    current_segment_data_for_client['audio_path'] = audio_file_path
                    successful_audio_count += 1
                except Exception as e:
                    print(f"  Error menyimpan audio untuk chunk {idx+1}: {e}")
                    failed_audio_count += 1
                    audio_file_path = None # Pastikan path None jika gagal simpan
            else:
                print(f"  Generasi audio untuk chunk {idx+1} gagal atau terkena kebijakan.")
                failed_audio_count += 1
            # === AKHIR PERBAIKAN UTAMA ===

            api_delay(int(os.environ.get("TTS_API_DELAY", 10)))

            num_images_target_for_chunk = random.randint(images_per_chunk_min_input, images_per_chunk_max_input)
            image_prompts_for_chunk = []

            if ai_provider == 'puter_ai_chat':
                if client_generated_image_prompts_parsed:
                    for prompt_set in client_generated_image_prompts_parsed:
                        if prompt_set.get('segment_index') == idx: image_prompts_for_chunk = prompt_set.get('prompts', []); break
                current_segment_data_for_client['num_images_target'] = len(image_prompts_for_chunk)
                print(f"  Menggunakan {len(image_prompts_for_chunk)} prompt gambar dari klien untuk chunk {idx+1} (Puter AI).")
            
            else:
                current_segment_data_for_client['num_images_target'] = num_images_target_for_chunk
                total_individual_prompts_attempted += num_images_target_for_chunk
                image_prompt_template_id_from_form = data.get('image_prompt_template_id')
                current_image_template = ptu.get_template_by_id(image_prompt_template_id_from_form)
                if not current_image_template or current_image_template.get('type') != 'image':
                    for tpl_def in ptu.load_prompt_templates():
                        if tpl_def.get('is_default') and tpl_def.get('type') == 'image': current_image_template = tpl_def; break
                if not current_image_template: print(f"  Peringatan: Tidak ada template prompt gambar valid untuk chunk {idx+1}. Prompt gambar akan kosong.")
                else:
                    # Gunakan teks yang sudah ditulis ulang jika ada untuk konsistensi
                    text_for_image_prompt = current_segment_data_for_client['chunk_text']
                    
                    if ai_provider == 'gemini':
                        print(f"  Membuat {num_images_target_for_chunk} prompt gambar dengan Gemini (server)...")
                        if not gemini_api_key: print("  Peringatan: Gemini API Key tidak ada untuk prompt gambar.")
                        else:
                            # PERBAIKAN: Gunakan model yang dipilih untuk prompt gambar juga
                            image_prompts_for_chunk = gemini_handler.generate_image_prompts_for_paragraph(
                                model_name=data.get('gemini_model', DEFAULT_GEMINI_MODEL), 
                                current_chunk_text=text_for_image_prompt, num_prompts_target=num_images_target_for_chunk, 
                                character_details=character_description, language="Inggris", 
                                previous_chunk_text=previous_chunk_for_context, template_content=current_image_template['content'] 
                            )
                    elif ai_provider == 'pollinations':
                        print(f"  Membuat {num_images_target_for_chunk} prompt gambar dengan Pollinations Text (server)...")
                        # PERBAIKAN: Gunakan model yang dipilih untuk prompt gambar juga
                        image_prompts_for_chunk = pollinations_text_handler.generate_image_prompts_via_pollinations(
                            model_name=data.get('pollinations_text_model', DEFAULT_POLLINATIONS_TEXT_MODEL),
                            current_chunk_text=text_for_image_prompt, num_prompts_target=num_images_target_for_chunk,
                            character_details=character_description, language_of_chunk=narrative_language, 
                            output_language="Inggris", previous_chunk_text=previous_chunk_for_context,
                            template_content=current_image_template['content'] 
                        )
            
            current_segment_data_for_client['image_prompts'] = image_prompts_for_chunk
            if image_prompts_for_chunk: successful_prompt_sets_count += 1; total_individual_prompts_generated += len(image_prompts_for_chunk)
            else: failed_prompt_sets_count +=1
            
            previous_chunk_for_context = current_segment_data_for_client['chunk_text']  # Gunakan teks yang sudah diproses
            if ai_provider != 'puter_ai_chat': api_delay(int(os.environ.get("PROMPT_API_DELAY", 1))) 
            
            # PERUBAHAN UTAMA: Selalu masukkan segmen jika ada audio, bahkan tanpa gambar
            if current_segment_data_for_client['audio_path']: 
                segments_for_client_generation.append(current_segment_data_for_client)
                print(f"  Segmen {idx + 1} ditambahkan ke daftar pemrosesan (audio: ada, gambar: {len(image_prompts_for_chunk)}).")
            else: 
                print(f"  Segmen {idx + 1} dilewati karena audio gagal.")
        
        report_phase1_2 = {
            "total_chunks_processed": len(text_chunks), "audio_generated_successfully": successful_audio_count, "audio_generation_failed": failed_audio_count,
            "texts_rewritten_for_tts": rewritten_text_count, "image_prompt_sets_generated_successfully": successful_prompt_sets_count, "image_prompt_sets_failed": failed_prompt_sets_count,
            "total_individual_prompts_generated": total_individual_prompts_generated,
            "total_individual_prompts_attempted": total_individual_prompts_attempted if ai_provider != 'puter_ai_chat' else "N/A (Client-gen)",
            "total_individual_prompts_failed": (total_individual_prompts_attempted - total_individual_prompts_generated) if ai_provider != 'puter_ai_chat' else "N/A (Client-gen)"
        }
        print("\n--- LAPORAN TAHAP 1 & 2 (Narasi, Audio & Prompt Gambar) ---")
        for key, value in report_phase1_2.items(): print(f"  {key.replace('_', ' ').capitalize()}: {value}")
        
        if not segments_for_client_generation: 
            return jsonify({"error": "Tidak ada segmen yang berhasil diproses untuk generasi klien.", "report": report_phase1_2}), 500
        
        response_data = {
            "message": "Narasi, audio, dan prompt gambar berhasil diproses. Lanjutkan ke generasi gambar di klien.",
            "segments_to_process": segments_for_client_generation,
            "report_phase1": report_phase1_2 
        }
        if narrative_source == 'prompt': 
             response_data["full_story_text_preview"] = full_story_text[:1000] + ("..." if len(full_story_text) > 1000 else "")
        
        return jsonify(response_data)

    except Exception as e:
        print(f"Error tidak terduga di endpoint /generate_media_prompts: {e}")
        import traceback; traceback.print_exc() 
        return jsonify({"error": f"Terjadi kesalahan internal: {str(e)}", "report": {"error_message": str(e)}}), 500

def handle_enhanced_processing(data, files, ai_provider, narrative_source):
    """
    Handle enhanced processing dengan logika level kalimat.
    """
    try:
        # Konfigurasi API
        gemini_api_key = None
        if ai_provider == 'gemini':
            gemini_api_key = data.get('gemini_api_key', os.environ.get('GEMINI_API_KEY'))
            if not gemini_api_key:
                return jsonify({"error": "Gemini API Key dibutuhkan untuk enhanced processing."}), 400
            if not gemini_handler.configure_gemini(gemini_api_key):
                return jsonify({"error": "Konfigurasi Gemini API Key gagal."}), 500

        # Parameter dengan Voice dan Style
        narrative_language = data.get('narrative_language', DEFAULT_NARRATIVE_LANGUAGE)
        character_description = data.get('character_description', '')
        tts_voice = data.get('tts_voice', DEFAULT_POLLINATIONS_VOICE)
        tts_voice_style = data.get('tts_voice_style', DEFAULT_POLLINATIONS_VOICE_STYLE)
        tts_max_retries = int(data.get('tts_max_retries', DEFAULT_TTS_MAX_RETRIES))
        
        # PERBAIKAN: Gunakan voice style yang lebih aman untuk enhanced processing
        if tts_voice_style in ["horror_story", "noir_detective"]:
            print(f"Enhanced Processing: Voice style '{tts_voice_style}' berisiko, akan menggunakan fallback jika diperlukan.")
        
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
            print("Enhanced: Membaca narasi dari file...")
            if 'narrative_file' not in files or not files.getlist('narrative_file')[0].filename:
                return jsonify({"error": "Tidak ada file narasi yang dipilih."}), 400
            
            full_story_text_parts = []
            for uploaded_file in files.getlist('narrative_file'):
                if uploaded_file and uploaded_file.filename.endswith('.txt'):
                    try:
                        filename = secure_filename(uploaded_file.filename)
                        unique_filename_part = generate_unique_filename(prefix=os.path.splitext(filename)[0], extension="txt")
                        uploaded_filepath_part = get_media_path(UPLOADED_NARRATIVES_DIR, unique_filename_part)
                        uploaded_file.save(uploaded_filepath_part)
                        with open(uploaded_filepath_part, "r", encoding="utf-8") as f_part:
                            full_story_text_parts.append(f_part.read())
                    except Exception as e:
                        print(f"Error memproses file '{uploaded_file.filename}': {e}")
            
            if not full_story_text_parts:
                return jsonify({"error": "Tidak ada file narasi .txt yang valid."}), 400
            
            full_story_text = "\n\n".join(full_story_text_parts)
            
        elif narrative_source == 'prompt':
            print("Enhanced: Generating narasi dari prompt...")
            story_prompt_input = data.get('story_prompt')
            if not story_prompt_input:
                return jsonify({"error": "Story prompt kosong."}), 400
            
            # Generate story
            if ai_provider == 'gemini':
                selected_model = data.get('gemini_model', DEFAULT_GEMINI_MODEL)
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
                selected_model = data.get('pollinations_text_model', DEFAULT_POLLINATIONS_TEXT_MODEL)
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
            return jsonify({"error": "Gagal mendapatkan teks narasi untuk enhanced processing."}), 500

        print(f"Enhanced: Teks narasi didapat: {len(full_story_text)} karakter")

        # Pecah menjadi paragraf dan kalimat
        print("Enhanced: Memecah teks menjadi paragraf dan kalimat...")
        paragraph_chunks = split_text_into_sentence_chunks(full_story_text, max_chars_per_chunk=600)
        
        if not paragraph_chunks:
            return jsonify({"error": "Gagal memecah teks menjadi paragraf dan kalimat."}), 500

        print(f"Enhanced: Berhasil memecah menjadi {len(paragraph_chunks)} paragraf")
        for i, (para, sentences) in enumerate(paragraph_chunks):
            print(f"  Paragraf {i+1}: {len(sentences)} kalimat, {len(para)} karakter")

        # Process dengan sentence-level logic
        image_template_id = data.get('image_prompt_template_id')
        image_template = ptu.get_template_by_id(image_template_id) if image_template_id else None
        template_content = image_template['content'] if image_template else None

        processed_segments = process_sentence_level_media_generation(
            paragraph_chunks=paragraph_chunks,
            ai_provider=ai_provider,
            gemini_handler_module=gemini_handler,
            pollinations_text_handler_module=pollinations_text_handler,
            character_description=character_description,
            language="Inggris",
            template_content=template_content
        )

        # Generate TTS untuk setiap paragraf dengan Voice dan Style
        print("Enhanced: Generating TTS untuk setiap paragraf...")
        segments_with_audio = []
        successful_audio_count = 0
        failed_audio_count = 0

        for segment in processed_segments:
            paragraph_text = segment['paragraph_text']
            print(f"Enhanced TTS untuk paragraf {segment['segment_index'] + 1}...")

            # PERBAIKAN: Panggilan TTS dengan voice dan style yang sudah diperbaiki
            audio_content = pollinations_tts_handler.generate_audio_from_text(
                text_input=paragraph_text,
                bahasa=bahasa_code_for_tts,
                voice=tts_voice,
                voice_style=tts_voice_style,
                max_retries_override=tts_max_retries
            )

            # PERBAIKAN: Gunakan provider yang benar untuk rewrite dalam enhanced processing
            if audio_content == CONTENT_POLICY_ERROR_SIGNAL:
                print(f"  Enhanced: Paragraf {segment['segment_index'] + 1} terkena kebijakan konten.")
                
                rewritten_text = rewrite_text_for_content_policy_with_provider(
                    ai_provider, paragraph_text, narrative_language, data
                )
                
                if rewritten_text:
                    # Gunakan voice style yang lebih aman untuk teks yang sudah ditulis ulang
                    safe_voice_style = "friendly" if tts_voice_style in ["horror_story", "noir_detective"] else tts_voice_style
                    
                    audio_content = pollinations_tts_handler.generate_audio_from_text(
                        text_input=rewritten_text,
                        bahasa=bahasa_code_for_tts,
                        voice=tts_voice,
                        voice_style=safe_voice_style,
                        max_retries_override=tts_max_retries
                    )
                    
                    # Update paragraph text dengan yang sudah ditulis ulang
                    if audio_content and audio_content != CONTENT_POLICY_ERROR_SIGNAL:
                        segment['paragraph_text'] = rewritten_text

            if audio_content and audio_content != CONTENT_POLICY_ERROR_SIGNAL:
                try:
                    audio_filename = generate_unique_filename(prefix="enhanced_tts", extension="mp3")
                    audio_file_path = get_media_path("audio", audio_filename)
                    with open(audio_file_path, 'wb') as f:
                        f.write(audio_content)

                    segment['audio_path'] = audio_file_path
                    segments_with_audio.append(segment)
                    successful_audio_count += 1
                    print(f"  Enhanced: Audio berhasil disimpan: {audio_file_path}")
                except Exception as e:
                    print(f"  Enhanced: Error menyimpan audio: {e}")
                    failed_audio_count += 1
            else:
                print(f"  Enhanced: Gagal generate audio untuk paragraf {segment['segment_index'] + 1}")
                failed_audio_count += 1

            api_delay(2)

        # Buat laporan enhanced
        report = {
            "processing_type": "Enhanced (Sentence-Level)",
            "total_paragraphs_processed": len(paragraph_chunks),
            "total_sentences_processed": sum(len(sentences) for _, sentences in paragraph_chunks),
            "total_image_prompts_generated": sum(len(seg['image_prompts']) for seg in processed_segments),
            "audio_generated_successfully": successful_audio_count,
            "audio_generation_failed": failed_audio_count,
            "segments_ready_for_video": len(segments_with_audio)
        }

        print("\n--- Enhanced Processing Report ---")
        for key, value in report.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        if not segments_with_audio:
            return jsonify({
                "error": "Enhanced processing: Tidak ada segmen yang berhasil diproses dengan audio.",
                "report": report
            }), 500

        return jsonify({
            "message": "Enhanced processing berhasil dengan logika level kalimat.",
            "segments_to_process": segments_with_audio,
            "report_phase1": report,
            "full_story_text_preview": full_story_text[:1000] + ("..." if len(full_story_text) > 1000 else "")
        })

    except Exception as e:
        print(f"Error dalam enhanced processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Enhanced processing error: {str(e)}"}), 500

@bp.route('/create_final_video', methods=['POST'])
def create_final_video_route():
    try:
        data_payload = request.get_json() 
        if not data_payload: return jsonify({"error": "Permintaan tidak memiliki data JSON."}), 400

        story_segments_with_images = data_payload.get('story_segments_with_images')
        effect_settings = data_payload.get('effect_settings')
        pollinations_image_model = data_payload.get('pollinations_image_model')
        aspect_ratio_str = data_payload.get('aspect_ratio', DEFAULT_IMAGE_ASPECT_RATIO_UI)
        print(f"DEBUG ROUTES: Aspek rasio diterima di /create_final_video: {aspect_ratio_str}") 
        image_max_retries = int(data_payload.get('image_max_retries', DEFAULT_IMAGE_MAX_RETRIES))
        
        # TAMBAHAN BARU: Ambil setting GPU acceleration dari client
        gpu_acceleration_enabled = data_payload.get('gpu_acceleration_enabled', DEFAULT_GPU_ACCELERATION_ENABLED)
        print(f"GPU Acceleration setting: {gpu_acceleration_enabled}")

        if not story_segments_with_images: return jsonify({"error": "Tidak ada data segmen cerita atau gambar yang diterima."}), 400
        
        final_segments_for_video_creator = []
        successful_image_saves_count = 0; failed_image_saves_count = 0
        
        print(f"\n--- TAHAP 3: GENERASI GAMBAR (Provider: Pollinations) ---")
        for segment in story_segments_with_images:
            audio_path = segment.get('audio_path')
            image_prompts_for_segment = segment.get('image_prompts', []) 
            chunk_text = segment.get('chunk_text', '') 
            
            if not audio_path or not os.path.exists(audio_path):
                print(f"  Segmen dilewati: Audio path tidak valid atau tidak ada untuk chunk '{chunk_text[:50]}...'."); continue

            saved_image_paths = []
            
            # PERUBAHAN UTAMA: Jika tidak ada prompt gambar, buat gambar placeholder atau skip gambar
            if not image_prompts_for_segment:
                print(f"  Segmen {segment.get('segment_index', 'unknown')} tidak memiliki prompt gambar, tetapi tetap diproses dengan audio saja.")
                # Tetap masukkan segmen ke video creator meskipun tanpa gambar
                final_segments_for_video_creator.append({
                    'chunk_text': chunk_text, 
                    'audio_path': audio_path, 
                    'image_paths': []  # List kosong untuk gambar
                })
                continue
            
            for img_idx, img_prompt_text in enumerate(image_prompts_for_segment):
                print(f"  Mencoba Pollinations gambar ({img_idx+1}) untuk segmen {segment['segment_index']}: {img_prompt_text[:50]}...")
                image_file_path = pollinations_image_handler.generate_image_pollinations(
                    prompt=img_prompt_text, aspect_ratio_str=aspect_ratio_str, image_model=pollinations_image_model, 
                    nologo=True, private=True, enhance=True, max_retries_override=image_max_retries 
                )
                if image_file_path: saved_image_paths.append(image_file_path); successful_image_saves_count += 1
                else: failed_image_saves_count += 1
                api_delay(int(os.environ.get("IMAGE_API_DELAY", 5))) 

            # PERUBAHAN: Selalu masukkan segmen jika ada audio, bahkan jika tidak ada gambar yang berhasil
            final_segments_for_video_creator.append({
                'chunk_text': chunk_text, 
                'audio_path': audio_path, 
                'image_paths': saved_image_paths
            })
            
            if saved_image_paths:
                print(f"  Segmen {segment.get('segment_index', 'unknown')} berhasil dengan {len(saved_image_paths)} gambar.")
            else:
                print(f"  Segmen {segment.get('segment_index', 'unknown')} tidak memiliki gambar, tetapi tetap diproses dengan audio.")

        report_phase3 = { "segments_received_for_image_gen": len(story_segments_with_images),
            "successful_image_generations": successful_image_saves_count, "failed_image_generations": failed_image_saves_count,
            "segments_ready_for_video_creation": len(final_segments_for_video_creator)
        }
        print("\n--- LAPORAN TAHAP 3 (Generasi Gambar Pollinations) ---")
        for key, value in report_phase3.items(): print(f"  {key.replace('_', ' ').capitalize()}: {value}")

        if not final_segments_for_video_creator:
            return jsonify({"error": "Tidak ada segmen dengan audio untuk pembuatan video.", "report": report_phase3}), 500

        print("\n--- TAHAP 4: MERANGKAI VIDEO AKHIR ---")
        final_video_path = video_creator.create_video_from_parts(
            final_segments_for_video_creator, 
            aspect_ratio_str=aspect_ratio_str, 
            effect_settings=effect_settings,
            gpu_acceleration_enabled=gpu_acceleration_enabled
        ) 
        
        if final_video_path:
            base_video_name = os.path.basename(final_video_path)
            relative_video_url = url_for('static', filename=f"generated_media/videos/{base_video_name}")
            return jsonify({"message": "Video berhasil dibuat!", "video_url": relative_video_url, "report": report_phase3 })
        else: 
            return jsonify({"error": "Gagal membuat video final.", "report": report_phase3}), 500

    except Exception as e:
        print(f"Error tidak terduga di endpoint /create_final_video: {e}")
        import traceback; traceback.print_exc() 
        return jsonify({"error": f"Terjadi kesalahan internal: {str(e)}", "report": {"error_message": str(e)}}), 500