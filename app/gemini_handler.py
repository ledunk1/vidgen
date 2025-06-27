import google.generativeai as genai
import os
import re 
import json # Ditambahkan untuk parsing JSON
import ast  # Ditambahkan untuk parsing list literal
from app.utils import api_delay, DEFAULT_GEMINI_MODEL 

def configure_gemini(api_key):
    """Konfigurasi API Key Gemini."""
    if api_key:
        genai.configure(api_key=api_key)
        return True
    else:
        print("Peringatan: GEMINI_API_KEY tidak disediakan atau tidak ditemukan.")
        return False

def generate_text_content(model_name, prompt_text, temperature=0.7, max_output_tokens=8192):
    """
    Menghasilkan teks menggunakan model Gemini yang dipilih.
    Mengembalikan string atau None.
    """
    try:
        effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
        model = genai.GenerativeModel(effective_model_name)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        response = model.generate_content(
            prompt_text,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            ),
            safety_settings=safety_settings 
        )
        if not response.candidates: 
             block_reason = response.prompt_feedback.block_reason if hasattr(response, 'prompt_feedback') and response.prompt_feedback else "Tidak diketahui (kandidat kosong)"
             print(f"Peringatan: Teks dari Gemini mungkin diblokir. Alasan: {block_reason}")
             return None
        
        # response.text seharusnya sudah menggabungkan semua parts jika ada
        return response.text
    except Exception as e:
        print(f"Error saat menghasilkan teks dengan Gemini ({model_name if model_name else DEFAULT_GEMINI_MODEL}): {e}")
        # Coba akses manual jika response.text gagal tapi ada kandidat
        if 'response' in locals() and hasattr(response, 'candidates') and response.candidates:
            try: 
                if response.candidates[0].content and response.candidates[0].content.parts:
                     return "".join(part.text for part in response.candidates[0].content.parts)
            except Exception as e_cand: 
                print(f"Tidak bisa mengambil teks dari kandidat setelah error awal: {e_cand}")
        return None 

def rewrite_text_for_content_policy(model_name, original_text, language="Indonesia", max_output_tokens=1024):
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
    prompt = (
        f"Tulis ulang teks berikut agar sepenuhnya mematuhi kebijakan konten Azure OpenAI dan aman untuk umum. "
        f"Hindari semua topik, bahasa, atau skenario yang mungkin dianggap sensitif, menyinggung, atau berbahaya. "
        f"Pertahankan makna inti, konteks, dan alur cerita dari teks asli semaksimal mungkin. "
        f"Teks harus dalam bahasa {language}.\n\n"
        f"Teks Asli yang Perlu Ditulis Ulang:\n\"\"\"\n{original_text}\n\"\"\"\n\n"
        f"Teks Hasil Penulisan Ulang (hanya teks hasil, tanpa tambahan komentar):\n"
    )
    print(f"Meminta Gemini ({effective_model_name}) untuk menulis ulang teks demi kebijakan konten (Bahasa: {language})...")
    try:
        rewritten_text = generate_text_content(effective_model_name, prompt, temperature=0.5, max_output_tokens=max_output_tokens)
        if rewritten_text:
            print("Teks berhasil ditulis ulang oleh Gemini.")
            return rewritten_text.strip()
        else:
            print("Gagal mendapatkan hasil penulisan ulang dari Gemini (hasil kosong).")
            return None
    except Exception as e:
        print(f"Error saat meminta penulisan ulang teks ke Gemini: {e}")
        return None

def summarize_text(model_name, text_to_summarize, max_summary_words=200, language="Indonesia"):
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
    prompt = (
        f"Ringkaslah teks berikut dalam kurang lebih {max_summary_words} kata. "
        f"Fokus pada poin-poin utama dan alur cerita untuk menjaga kontinuitas di bagian cerita selanjutnya. "
        f"Pastikan ringkasan mematuhi kebijakan konten standar dan aman untuk umum, hindari topik sensitif. "
        f"Ringkasan harus dalam bahasa {language}.\n\n"
        f"Teks:\n{text_to_summarize}"
    )
    try:
        summary = generate_text_content(effective_model_name, prompt, temperature=0.5, max_output_tokens=1024)
        return summary
    except Exception as e:
        print(f"Error saat meringkas teks dengan Gemini ({effective_model_name}): {e}")
        return None

def generate_image_prompts_for_paragraph(
    model_name, 
    current_chunk_text, 
    num_prompts_target, 
    character_details=None, 
    language="Inggris", 
    previous_chunk_text=None,
    template_content=None
):
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL

    if template_content:
        prompt_instruction = template_content.format(
            language=language, current_chunk_text=current_chunk_text,
            previous_chunk_text=previous_chunk_text if previous_chunk_text else "Tidak ada konteks sebelumnya.",
            character_description=character_details if character_details else "Tidak ada deskripsi karakter khusus.",
            num_prompts=num_prompts_target
        )
    else:
        prompt_instruction = (
            f"Anda adalah seorang asisten yang bertugas membuat prompt gambar yang sangat deskriptif untuk AI image generator. "
            f"Prompt gambar yang dihasilkan harus dalam bahasa {language}.\n\n"
        )
        if previous_chunk_text:
            prompt_instruction += f"Konteks dari narasi sebelumnya:\n\"\"\"\n{previous_chunk_text[:300]}...\n\"\"\"\n\n" 
        prompt_instruction += (
            f"Berdasarkan narasi saat ini, buatlah persis {num_prompts_target} prompt gambar yang berbeda. "
            f"Setiap prompt harus fokus pada aspek visual yang berbeda. Pastikan aman untuk umum.\n"
        )
        if character_details:
            prompt_instruction += f"Konsistensi karakter: {character_details}. Sebutkan detail ini jika relevan.\n"
        prompt_instruction += (
            "Format output HARUS berupa daftar bernomor, masing-masing di baris baru. Contoh:\n"
            "1. [Prompt gambar 1]\n"
            f"{num_prompts_target}. [Prompt gambar {num_prompts_target}]\n\n"
            f"Narasi Saat Ini:\n\"\"\"\n{current_chunk_text}\n\"\"\""
        )

    try:
        print(f"Meminta {num_prompts_target} prompt gambar dari Gemini ({effective_model_name}) untuk chunk: {current_chunk_text[:70]}...")
        
        raw_prompts_text = generate_text_content(effective_model_name, prompt_instruction, temperature=0.8, max_output_tokens=2048) # Max token bisa disesuaikan
        
        if not raw_prompts_text: 
            print("Tidak ada output teks dari Gemini untuk prompt gambar.")
            return []
        
        print(f"Output mentah untuk prompt gambar dari Gemini (tipe: {type(raw_prompts_text)}):\n{str(raw_prompts_text)[:500]}")
        extracted_prompts = []
        parsed_successfully = False

        if isinstance(raw_prompts_text, str):
            cleaned_output_str = raw_prompts_text.strip()
            # Hapus markdown code block jika ada
            if cleaned_output_str.startswith("```json"): cleaned_output_str = cleaned_output_str[7:]
            if cleaned_output_str.startswith("```"): cleaned_output_str = cleaned_output_str[3:]
            if cleaned_output_str.endswith("```"): cleaned_output_str = cleaned_output_str[:-3]
            cleaned_output_str = cleaned_output_str.strip()

            # 1. Coba parse sebagai JSON array
            try:
                if cleaned_output_str.startswith('[') and cleaned_output_str.endswith(']'):
                    potential_list = json.loads(cleaned_output_str)
                    if isinstance(potential_list, list) and all(isinstance(item, str) for item in potential_list):
                        print("Berhasil parse output Gemini sebagai JSON list.")
                        extracted_prompts = [p.strip() for p in potential_list if p.strip()]
                        parsed_successfully = True
                # else:
                #     print("String dari Gemini tidak terlihat seperti JSON array, melewati parsing JSON.")
            except json.JSONDecodeError:
                print("Gagal parse output Gemini sebagai JSON list, mencoba ast.literal_eval.")
            
            # 2. Jika JSON gagal, coba ast.literal_eval
            if not parsed_successfully:
                try:
                    if cleaned_output_str.startswith('[') and cleaned_output_str.endswith(']'):
                        potential_list = ast.literal_eval(cleaned_output_str)
                        if isinstance(potential_list, list) and all(isinstance(item, str) for item in potential_list):
                            print("Berhasil parse output Gemini sebagai Python list literal (ast.literal_eval).")
                            extracted_prompts = [p.strip() for p in potential_list if p.strip()]
                            parsed_successfully = True
                    # else:
                    #     print("String dari Gemini tidak terlihat seperti Python list literal, melewati ast.literal_eval.")
                except (ValueError, SyntaxError, TypeError) as e_eval:
                    print(f"Gagal parse output Gemini sebagai list literal ({e_eval}).")

            # 3. Jika semua parsing gagal, fallback ke regex dan splitlines
            if not parsed_successfully:
                print("Fallback Gemini: Mencari pola nomor atau membagi per baris.")
                found_numbered = re.findall(r"^\s*\d+\.\s*(.+)$", raw_prompts_text, re.MULTILINE) 
                if found_numbered:
                    print(f"Ditemukan {len(found_numbered)} prompt bernomor dari Gemini.")
                    for p_text in found_numbered: extracted_prompts.append(p_text.strip())
                else: 
                    print("Tidak ada prompt bernomor dari Gemini. Mencoba membagi berdasarkan baris baru pada teks yang sudah dibersihkan.")
                    lines = cleaned_output_str.splitlines() # Gunakan cleaned_output_str untuk splitlines
                    for line in lines:
                        final_cleaned_line = line.strip()
                        if final_cleaned_line and len(final_cleaned_line) > 15 and \
                           not final_cleaned_line.lower().startswith(("berikut adalah", "daftar prompt", "output:", "```")) and \
                           not (final_cleaned_line.startswith('[') and final_cleaned_line.endswith(']')) and \
                           not (final_cleaned_line.startswith('{') and final_cleaned_line.endswith('}')):
                            extracted_prompts.append(final_cleaned_line)
        else:
            print(f"Tipe output tidak dikenal dari Gemini ({type(raw_prompts_text)}), tidak dapat mengekstrak prompt.")


        if not extracted_prompts: 
            print("Tidak ada prompt gambar yang berhasil diekstrak dari output Gemini.")
            return []
        
        final_prompts = extracted_prompts[:num_prompts_target]
        if len(final_prompts) < num_prompts_target:
            print(f"Peringatan: Gemini hanya menghasilkan/berhasil diekstrak {len(final_prompts)} prompt, kurang dari {num_prompts_target} yang diminta.")
        elif len(final_prompts) > num_prompts_target:
             print(f"Info: Gemini menghasilkan lebih banyak prompt ({len(final_prompts)}) dari yang diminta ({num_prompts_target}). Mengambil {num_prompts_target} pertama.")
        return final_prompts
    except Exception as e:
        print(f"Error saat menghasilkan atau memproses prompt gambar dengan Gemini ({effective_model_name}): {e}")
        return []

def generate_story_part_from_template(
    gemini_api_key, model_name, template_content,
    fill_data, part_number 
):
    if not configure_gemini(gemini_api_key): 
        return "Error: Gemini API Key tidak terkonfigurasi."

    previous_summary_block = ""
    if part_number > 1 and fill_data.get("previous_summary_content"):
        previous_summary_block = (
            f"Ini adalah bagian ke-{part_number} dari cerita. Berikut adalah ringkasan dari bagian sebelumnya "
            f"(pastikan ringkasan ini juga dalam bahasa {fill_data.get('language', 'Indonesia')}, mematuhi kebijakan konten, dan gaya yang diminta):\n"
            f"{fill_data['previous_summary_content']}\n\n"
        )

    character_description_block = ""
    if fill_data.get("character_description_content"):
        character_description_block = (
            f"Deskripsi Karakter (jika ada, pertahankan konsistensi dan pastikan deskripsi aman, sesuai gaya, dan relevan dengan bahasa {fill_data.get('language', 'Indonesia')}):\n"
            f"{fill_data['character_description_content']}\n\n"
        )
    
    final_fill_data = {
        "expertise": fill_data.get("expertise", "seorang pendongeng ulung"),
        "language": fill_data.get("language", "Indonesia"),
        "tone": fill_data.get("tone", "normal"),
        "format_style": fill_data.get("format_style", "narasi deskriptif"),
        "target_words": fill_data.get("target_words", "3500"),
        "azure_openai_policy_note": "PENTING: Buat narasi sesuai dengan kebijakan konten Azure OpenAI. Hindari topik, bahasa, atau skenario yang mungkin melanggar kebijakan konten tersebut. Fokus pada cerita yang aman untuk umum.",
        "previous_summary_block": previous_summary_block,
        "main_story_prompt": fill_data.get("main_story_prompt", ""),
        "character_description_block": character_description_block,
        "continuation_instruction": "Silakan tulis bagian cerita selanjutnya:"
    }

    final_prompt = template_content
    for key, value in final_fill_data.items():
        placeholder = f"{{{key}}}" 
        final_prompt = final_prompt.replace(placeholder, str(value)) 

    print(f"\n--- MENGHASILKAN BAGIAN CERITA KE-{part_number} MENGGUNAKAN TEMPLATE (Bahasa: {final_fill_data['language']}) ---")
    
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
    story_text = generate_text_content(effective_model_name, final_prompt)
    
    if story_text:
        print(f"Bagian cerita ke-{part_number} (dari template) berhasil dihasilkan (panjang: {len(story_text.split())} kata).")
    else:
        print(f"Gagal menghasilkan bagian cerita ke-{part_number} (dari template).")
        story_text = f"Error: Gagal menghasilkan teks untuk bagian ke-{part_number} menggunakan template."
    return story_text
