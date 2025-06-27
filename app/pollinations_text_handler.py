import requests
import urllib.parse
import json
import time
import re # Impor modul re untuk parsing
import ast # Ditambahkan untuk parsing string list
from app.utils import POLLINATIONS_TEXT_BASE_URL, POLLINATIONS_TEXT_API_DELAY_SECONDS

def generate_text_pollinations(
    main_prompt, 
    model="openai", 
    system_prompt=None, 
    private=True,
    max_retries=2,
    temperature=0.7,
    top_p=None,
    presence_penalty=None,
    frequency_penalty=None
    ):
    """
    Menghasilkan teks menggunakan API Text-to-Text Pollinations.
    Bisa mengembalikan string atau list of strings jika API mengembalikan JSON array.
    """
    if not main_prompt:
        print("Error: Prompt utama tidak boleh kosong untuk Pollinations Text API.")
        return None

    encoded_prompt = urllib.parse.quote(main_prompt)
    url = f"{POLLINATIONS_TEXT_BASE_URL}{encoded_prompt}"
    
    params = {
        "model": model,
        "json": "true", 
        "private": str(private).lower(),
        "temperature": temperature
    }
    if system_prompt:
        params["system"] = urllib.parse.quote(system_prompt)
    if top_p is not None:
        params["top_p"] = top_p
    if presence_penalty is not None:
        params["presence_penalty"] = presence_penalty
    if frequency_penalty is not None:
        params["frequency_penalty"] = frequency_penalty
    
    last_exception = None
    for attempt in range(1, max_retries + 1):
        print(f"Memanggil API Pollinations Text (Percobaan ke-{attempt}/{max_retries}): Model={model}, Prompt='{main_prompt[:70]}...'")
        try:
            response = requests.get(url, params=params, timeout=120) 
            response.raise_for_status()

            try:
                data_text = response.text
                try:
                    data = json.loads(data_text)
                except json.JSONDecodeError:
                    print(f"Peringatan: Respons Pollinations Text bukan JSON valid. Mengembalikan sebagai teks biasa. Respons: {data_text[:200]}")
                    return data_text.strip() 

                generated_output = None
                if isinstance(data, dict):
                    if "text" in data: generated_output = data["text"]
                    elif "output" in data: generated_output = data["output"]
                    elif "response" in data: generated_output = data["response"]
                    elif "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0 and "text" in data["choices"][0]:
                        generated_output = data["choices"][0]["text"]
                    elif "data" in data and isinstance(data["data"], str) : 
                        generated_output = data["data"]
                    # Kasus baru: jika "data" adalah list of strings (misalnya untuk prompt gambar)
                    elif "data" in data and isinstance(data["data"], list) and all(isinstance(item, str) for item in data["data"]):
                        generated_output = data["data"]
                    else: 
                        if len(data) == 1: 
                            generated_output = str(list(data.values())[0])
                        else: 
                             generated_output = data_text # Kembalikan JSON string jika tidak ada field yang cocok
                elif isinstance(data, str): 
                    generated_output = data
                # Kasus baru: jika root JSON adalah list of strings
                elif isinstance(data, list) and all(isinstance(item, str) for item in data):
                    generated_output = data
                else: 
                    generated_output = data_text # Fallback

                if generated_output is not None:
                    print(f"Teks/Data berhasil dihasilkan oleh Pollinations Text API (Model: {model}). Tipe data: {type(generated_output)}")
                    # Jika hasilnya adalah list, kembalikan list tersebut. Jika string, strip.
                    return generated_output if isinstance(generated_output, list) else str(generated_output).strip()
                else:
                    print(f"Gagal mengekstrak teks/data dari respons JSON Pollinations: {data}")
                    last_exception = Exception("Format JSON tidak dikenali atau tidak ada teks/data.")

            except Exception as e_parse:
                print(f"Error memproses respons dari Pollinations Text: {e_parse}")
                last_exception = e_parse

        except requests.exceptions.RequestException as e:
            print(f"Error memanggil API Pollinations Text pada percobaan ke-{attempt}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Detail Error: Status {e.response.status_code}, Respon: {e.response.text[:200]}")
            last_exception = e
        except Exception as e_general:
            print(f"Error umum saat proses Pollinations Text pada percobaan ke-{attempt}: {e_general}")
            last_exception = e_general
        
        if attempt < max_retries:
            print(f"Menunggu {POLLINATIONS_TEXT_API_DELAY_SECONDS + attempt} detik sebelum mencoba lagi...")
            time.sleep(POLLINATIONS_TEXT_API_DELAY_SECONDS + attempt)
        else:
            print(f"Gagal menghasilkan teks dari Pollinations setelah {max_retries} percobaan.")
            if last_exception: print(f"Error terakhir: {last_exception}")
            return None
    return None


def summarize_text_pollinations(
    text_to_summarize, 
    model="openai-fast", 
    language="Indonesia", 
    max_summary_words=150,
    private=True
    ):
    main_prompt_for_summary = (
        f"Dalam bahasa {language}, ringkaslah teks berikut menjadi sekitar {max_summary_words} kata. "
        f"Fokus pada poin-poin utama dan alur cerita. "
        f"Pastikan ringkasan aman untuk umum.\n\n"
        f"Teks yang akan diringkas:\n\"\"\"\n{text_to_summarize[:1500]}\n\"\"\""
    )
    system_prompt_for_summary = f"Anda adalah asisten AI yang ahli dalam membuat ringkasan teks dalam berbagai bahasa dan memastikan konten aman."
    print(f"Meminta ringkasan dari Pollinations Text API (Model: {model})...")
    summary_result = generate_text_pollinations(
        main_prompt=main_prompt_for_summary, model=model,
        system_prompt=system_prompt_for_summary, private=private, temperature=0.5
    )
    if summary_result and isinstance(summary_result, str): # Pastikan ringkasan adalah string
        print("Ringkasan berhasil dibuat oleh Pollinations Text API.")
        return summary_result
    else:
        print(f"Gagal membuat ringkasan atau format tidak sesuai. Hasil: {summary_result}")
    return None


def generate_image_prompts_via_pollinations(
    model_name, 
    current_chunk_text, 
    num_prompts_target, 
    character_details=None, 
    language_of_chunk="Indonesia",
    output_language="Inggris",
    previous_chunk_text=None,
    private=True,
    template_content=None
):
    system_prompt_for_img = ""
    if template_content:
        main_prompt_for_img = template_content.format(
            language=output_language, current_chunk_text=current_chunk_text,
            previous_chunk_text=previous_chunk_text if previous_chunk_text else "Tidak ada konteks sebelumnya.",
            character_description=character_details if character_details else "Tidak ada deskripsi karakter khusus.",
            num_prompts=num_prompts_target
        )
    else: 
        system_prompt_for_img = (
            f"Anda adalah AI yang sangat kreatif dan ahli dalam membuat prompt gambar yang detail dan visual untuk generator gambar AI. "
            f"Output Anda HARUS berupa daftar dari {num_prompts_target} prompt gambar dalam bahasa {output_language}. "
            f"Setiap prompt harus unik dan mendeskripsikan adegan atau elemen visual dari narasi yang diberikan. "
            f"Pastikan semua prompt aman untuk umum. "
            f"Format output: Jika memungkinkan, kembalikan sebagai list JSON dari string. Jika tidak, daftar bernomor (misal: 1. Prompt A)."
        )
        main_prompt_for_img = f"Narasi saat ini (bahasa {language_of_chunk}):\n\"\"\"\n{current_chunk_text}\n\"\"\"\n\n"
        if previous_chunk_text: main_prompt_for_img += f"Konteks sebelumnya (bahasa {language_of_chunk}):\n\"\"\"\n{previous_chunk_text[:300]}...\n\"\"\"\n\n"
        if character_details: main_prompt_for_img += f"Detail karakter:\n{character_details}\n\n"
        main_prompt_for_img += f"Buatlah {num_prompts_target} prompt gambar dalam bahasa {output_language}. Satu kalimat deskriptif per prompt. Hindari 'Gambar yang menunjukkan...'. "

    print(f"Meminta {num_prompts_target} prompt gambar dari Pollinations Text API (Model: {model_name})...")
    raw_output = generate_text_pollinations(
        main_prompt=main_prompt_for_img, model=model_name,
        system_prompt=system_prompt_for_img if not template_content and system_prompt_for_img else None,
        private=private, temperature=0.8
    )

    if not raw_output:
        print("Tidak ada output dari Pollinations untuk prompt gambar."); return []

    print(f"Output mentah untuk prompt gambar (tipe: {type(raw_output)}):\n{str(raw_output)[:500]}")
    
    extracted_prompts = []
    if isinstance(raw_output, list) and all(isinstance(item, str) for item in raw_output):
        print("Output sudah berupa list string, menggunakan langsung.")
        extracted_prompts = [p.strip() for p in raw_output if p.strip()]
    elif isinstance(raw_output, str):
        cleaned_output_str = raw_output.strip()
        # Hapus markdown code block jika ada
        if cleaned_output_str.startswith("```json"): cleaned_output_str = cleaned_output_str[7:]
        if cleaned_output_str.startswith("```"): cleaned_output_str = cleaned_output_str[3:]
        if cleaned_output_str.endswith("```"): cleaned_output_str = cleaned_output_str[:-3]
        cleaned_output_str = cleaned_output_str.strip()

        parsed_successfully = False
        # 1. Coba parse sebagai JSON array
        try:
            potential_list = json.loads(cleaned_output_str)
            if isinstance(potential_list, list) and all(isinstance(item, str) for item in potential_list):
                print("Berhasil parse output string sebagai JSON list.")
                extracted_prompts = [p.strip() for p in potential_list if p.strip()]
                parsed_successfully = True
        except json.JSONDecodeError:
            print("Gagal parse sebagai JSON list, mencoba ast.literal_eval.")
        
        # 2. Jika JSON gagal, coba ast.literal_eval
        if not parsed_successfully:
            try:
                potential_list = ast.literal_eval(cleaned_output_str)
                if isinstance(potential_list, list) and all(isinstance(item, str) for item in potential_list):
                    print("Berhasil parse output string sebagai Python list literal (ast.literal_eval).")
                    extracted_prompts = [p.strip() for p in potential_list if p.strip()]
                    parsed_successfully = True
                else:
                    print("Hasil ast.literal_eval bukan list string.")
            except (ValueError, SyntaxError, TypeError) as e_eval:
                print(f"Gagal parse output sebagai list literal ({e_eval}).")

        # 3. Jika semua parsing gagal, fallback ke regex dan splitlines
        if not parsed_successfully:
            print("Fallback: Mencari pola nomor atau membagi per baris.")
            found_numbered = re.findall(r"^\s*\d+\.\s*(.+)$", raw_output, re.MULTILINE) # Gunakan raw_output asli untuk regex
            if found_numbered:
                print(f"Ditemukan {len(found_numbered)} prompt bernomor.")
                for p_text in found_numbered: extracted_prompts.append(p_text.strip())
            else:
                print("Tidak ada prompt bernomor. Mencoba membagi berdasarkan baris baru.")
                lines = raw_output.splitlines()
                for line in lines:
                    cleaned_line = line.strip()
                    if cleaned_line and len(cleaned_line) > 15 and not cleaned_line.lower().startswith(("berikut adalah", "daftar prompt", "output:", "```")):
                        extracted_prompts.append(cleaned_line)
    else:
        print(f"Tipe output tidak dikenal ({type(raw_output)}), tidak dapat mengekstrak prompt.")

    if not extracted_prompts:
        print("Tidak ada prompt gambar yang berhasil diekstrak."); return []

    final_prompts = extracted_prompts[:num_prompts_target]
    if len(final_prompts) < num_prompts_target:
        print(f"Peringatan: Hanya {len(final_prompts)} prompt gambar yang diekstrak, kurang dari {num_prompts_target} yang diminta.")
    elif len(final_prompts) > num_prompts_target:
        print(f"Info: Lebih banyak prompt ({len(final_prompts)}) diekstrak dari yang diminta ({num_prompts_target}). Mengambil {num_prompts_target} pertama.")
    
    return final_prompts
