# app/pollinations_tts_handler.py

import requests
import time
import re
import json
import base64
from app.utils import api_delay
from urllib.parse import quote_plus

# Definisikan URL dasar API TTS Pollinations. 
# Kita akan menggunakan pendekatan sederhana yang menggabungkan teks ke URL.
POLLINATIONS_TTS_BASE_URL = "https://text.pollinations.ai/"
POLLINATIONS_TTS_OPENAI_URL = "https://text.pollinations.ai/openai"

# HARDCODED AUTH TOKEN - Dimasukkan langsung ke dalam script
POLLINATIONS_TTS_AUTH_TOKEN = "o42-4XkdeJgP95mm"

# Sinyal error untuk pelanggaran kebijakan konten.
CONTENT_POLICY_ERROR_SIGNAL = "CONTENT_POLICY_VIOLATION"

def sanitize_text_for_tts(text):
    """
    Membersihkan teks dari kata-kata yang mungkin memicu kebijakan konten TTS.
    """
    # Daftar kata-kata yang sering memicu kebijakan konten
    problematic_words = {
        # Kata-kata yang berhubungan dengan kekerasan atau ancaman
        'mengerikan': 'mengejutkan',
        'menyeramkan': 'aneh',
        'menakutkan': 'mengejutkan',
        'membunuh': 'mengalahkan',
        'mati': 'pingsan',
        'darah': 'cairan merah',
        'mayat': 'tubuh yang tidak bergerak',
        'hantu': 'sosok misterius',
        'setan': 'makhluk gelap',
        'iblis': 'entitas jahat',
        'kutukan': 'mantra',
        'terkutuk': 'terkena mantra',
        'membunuh': 'mengalahkan',
        'melukai': 'menyentuh',
        'menyiksa': 'mengganggu',
        'kekerasan': 'konflik',
        'brutal': 'kasar',
        'sadis': 'kejam',
        'bengis': 'galak',
        
        # Kata-kata yang berhubungan dengan horror/supernatural
        'berdarah': 'berwarna merah',
        'mencekam': 'menegangkan',
        'horor': 'misteri',
        'terror': 'ketakutan',
        'menghantui': 'mengikuti',
        'kerasukan': 'dipengaruhi',
        'jin': 'makhluk halus',
        'roh': 'jiwa',
        'arwah': 'roh',
        'pocong': 'sosok putih',
        'kuntilanak': 'wanita berambut panjang',
        'genderuwo': 'sosok besar',
        
        # Kata-kata emosional yang intens
        'panik': 'terkejut',
        'histeria': 'sangat terkejut',
        'trauma': 'terguncang',
        'shock': 'terkejut',
        'ngeri': 'aneh',
        'seram': 'misterius',
        'geram': 'kesal',
        'murka': 'marah',
        'amarah': 'kemarahan',
        
        # Kata-kata yang berhubungan dengan kegelapan/mistis
        'gelap gulita': 'sangat gelap',
        'kegelapan': 'tempat gelap',
        'kelam': 'gelap',
        'suram': 'redup',
        'mencekam': 'menegangkan',
        'menyeramkan': 'aneh',
        
        # Kata-kata yang berhubungan dengan tubuh/fisik yang sensitif
        'berlumuran': 'tertutup',
        'mengalir': 'menetes',
        'merembes': 'keluar perlahan',
        'membusuk': 'rusak',
        'busuk': 'rusak',
        'bangkai': 'sisa-sisa',
        
        # Kata-kata aksi yang agresif
        'menyerang': 'mendekati',
        'menerkam': 'melompat ke',
        'mencakar': 'menyentuh',
        'menggigit': 'menyentuh',
        'merobek': 'merusak',
        'menghancurkan': 'merusak',
        'memporak-porandakan': 'mengacaukan',
        
        # Kata-kata suara yang menakutkan
        'jeritan': 'teriakan',
        'pekikan': 'suara keras',
        'rintihan': 'suara lemah',
        'erangan': 'suara pelan',
        'meraung': 'bersuara keras',
        'mengaum': 'bersuara',
        'mendesis': 'berbisik',
        
        # Kata-kata kondisi ekstrem
        'sekarat': 'lemah',
        'tewas': 'tidak sadarkan diri',
        'binasa': 'hilang',
        'musnah': 'lenyap',
        'hancur': 'rusak',
        'remuk': 'pecah',
        'luluh': 'hancur',
        
        # Kata-kata yang berhubungan dengan penderitaan
        'menderita': 'mengalami kesulitan',
        'kesakitan': 'tidak nyaman',
        'tersiksa': 'terganggu',
        'sengsara': 'susah',
        'nestapa': 'kesedihan',
        'duka': 'sedih',
        'nestapa': 'kesulitan'
    }
    
    # Ganti kata-kata problematik
    sanitized_text = text
    for problematic, replacement in problematic_words.items():
        # Gunakan regex untuk mengganti kata dengan mempertimbangkan batas kata
        pattern = r'\b' + re.escape(problematic) + r'\b'
        sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
    
    # Bersihkan karakter khusus yang mungkin bermasalah
    sanitized_text = re.sub(r'[^\w\s\.,!?;:\-\(\)]', ' ', sanitized_text)
    
    # Bersihkan spasi berlebih
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
    
    return sanitized_text

def generate_audio_from_text_with_token(text_input, bahasa="id-ID", voice="nova", voice_style="friendly", 
                                       max_retries_override=2):
    """
    Menghasilkan audio dari teks menggunakan API Pollinations dengan auth token yang sudah hardcoded.
    Menggunakan format OpenAI-compatible API dengan Bearer token authentication.
    
    Args:
        text_input (str): Teks yang akan diubah menjadi suara.
        bahasa (str): Kode bahasa (cth: 'id-ID'). Digunakan untuk memilih voice.
        voice (str): Pilihan suara (cth: 'nova', 'alloy', 'shimmer', dll).
        voice_style (str): Gaya suara (cth: 'friendly', 'calm', dll).
        max_retries_override (int): Jumlah percobaan ulang jika gagal.

    Returns:
        - Audio content (binary) jika berhasil.
        - CONTENT_POLICY_ERROR_SIGNAL (str) jika ada pelanggaran kebijakan.
        - None jika terjadi error lain.
    """
    if not text_input or not text_input.strip():
        print("Error TTS: Teks input tidak boleh kosong.")
        return None

    # Sanitasi teks sebelum diproses
    sanitized_text = sanitize_text_for_tts(text_input)
    print(f"TTS: Teks asli: {text_input[:100]}...")
    print(f"TTS: Teks sanitasi: {sanitized_text[:100]}...")

    # Mapping bahasa untuk prompt yang sesuai
    language_prompts = {
        "id-ID": "Bacakan teks berikut dengan jelas dan natural:",
        "en-US": "Read the following text clearly and naturally:",
        "de-DE": "Lesen Sie den folgenden Text klar und natürlich vor:",
        "es-ES": "Lee el siguiente texto de forma clara y natural:",
        "fr-FR": "Lisez le texte suivant de manière claire et naturelle:",
        "ja-JP": "次のテキストを明確で自然に読んでください：",
        "ko-KR": "다음 텍스트를 명확하고 자연스럽게 읽어주세요:",
        "ar-SA": "اقرأ النص التالي بوضوح وطبيعية:",
        "zh-CN": "请清晰自然地朗读以下文本："
    }
    
    # Pilih prompt berdasarkan bahasa, default ke Indonesia jika tidak ada
    instruction_prompt = language_prompts.get(bahasa, language_prompts["id-ID"])
    
    # Gabungkan prompt instruksi dengan teks yang sudah disanitasi
    final_text_for_tts = f"{instruction_prompt} {sanitized_text}"
    
    # Daftar voice style yang lebih aman untuk fallback
    safe_voice_styles = ["friendly", "calm", "patient_teacher", "mellow_story"]
    
    # Jika voice style yang dipilih berpotensi bermasalah, gunakan yang lebih aman
    risky_styles = ["horror_story", "noir_detective"]
    if voice_style in risky_styles:
        print(f"TTS: Voice style '{voice_style}' mungkin berisiko, akan mencoba fallback jika gagal.")
    
    effective_max_retries = max(1, max_retries_override)
    
    # Selalu gunakan auth token yang sudah hardcoded
    print(f"TTS: Menggunakan auth token hardcoded untuk rate limit yang lebih tinggi")
    return _generate_audio_with_openai_api(
        final_text_for_tts, voice, voice_style, POLLINATIONS_TTS_AUTH_TOKEN, 
        effective_max_retries, safe_voice_styles, risky_styles
    )

def _generate_audio_with_openai_api(text, voice, voice_style, auth_token, max_retries, 
                                   safe_voice_styles, risky_styles):
    """
    Menggunakan OpenAI-compatible API dengan Bearer token authentication.
    """
    url = POLLINATIONS_TTS_OPENAI_URL
    
    # Payload sesuai format OpenAI API
    payload = {
        "model": "openai-audio",
        "modalities": ["text", "audio"],
        "audio": {
            "voice": voice,
            "format": "mp3"
        },
        "messages": [
            {
                "role": "user", 
                "content": text
            }
        ],
        "private": True  # Untuk privasi yang lebih baik
    }
    
    # Headers dengan Bearer token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    for attempt in range(1, max_retries + 1):
        print(f"TTS API dengan token (Percobaan ke-{attempt}/{max_retries}): Voice={voice}, Style={voice_style}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code >= 400:
                print(f"Error dari API dengan status code: {response.status_code}")
                error_text = response.text.lower()
                
                # Cek spesifik untuk error kebijakan konten
                if "content management policy" in error_text or "safety" in error_text or "content policy" in error_text:
                    print("Terdeteksi error kebijakan konten dari API dengan token.")
                    
                    # Jika ini percobaan pertama dan voice style berisiko, coba dengan style yang lebih aman
                    if attempt == 1 and voice_style in risky_styles:
                        print(f"Mencoba dengan voice style yang lebih aman...")
                        for safe_style in safe_voice_styles:
                            print(f"Mencoba dengan voice style: {safe_style}")
                            # Update payload dengan style yang lebih aman
                            safe_payload = payload.copy()
                            # Note: OpenAI API mungkin tidak mendukung voice_style secara langsung
                            # Kita bisa mencoba menambahkannya ke dalam content atau menggunakan voice yang berbeda
                            safe_payload["messages"][0]["content"] = f"[Style: {safe_style}] {text}"
                            
                            try:
                                safe_response = requests.post(url, json=safe_payload, headers=headers, timeout=120)
                                if safe_response.status_code == 200:
                                    response_data = safe_response.json()
                                    if "choices" in response_data and len(response_data["choices"]) > 0:
                                        choice = response_data["choices"][0]
                                        if "message" in choice and "audio" in choice["message"]:
                                            audio_base64 = choice["message"]["audio"]["data"]
                                            audio_binary = base64.b64decode(audio_base64)
                                            print(f"Berhasil dengan voice style: {safe_style}")
                                            return audio_binary
                            except Exception as e_safe:
                                print(f"Gagal dengan style {safe_style}: {e_safe}")
                                continue
                    
                    # Jika semua style gagal, return signal
                    return CONTENT_POLICY_ERROR_SIGNAL
                else:
                    print(f"Error lain dari API: {response.text[:200]}")
            
            # Jika berhasil (status 200)
            elif response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Parse response sesuai format OpenAI
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        choice = response_data["choices"][0]
                        if "message" in choice and "audio" in choice["message"]:
                            audio_base64 = choice["message"]["audio"]["data"]
                            audio_binary = base64.b64decode(audio_base64)
                            print(f"Audio berhasil didapatkan dari API dengan token (percobaan ke-{attempt})")
                            return audio_binary
                        else:
                            print(f"Format response tidak sesuai: {response_data}")
                    else:
                        print(f"Response tidak mengandung choices: {response_data}")
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON response: {e}")
                except Exception as e:
                    print(f"Error processing response: {e}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error koneksi saat menghubungi API TTS dengan token percobaan ke-{attempt}: {e}")
        
        # Jika loop belum berakhir, tunggu sebelum mencoba lagi
        if attempt < max_retries:
            api_delay(30)
    
    print(f"Gagal menghasilkan audio dengan token setelah {max_retries} percobaan.")
    return None

def _generate_audio_with_simple_api(text, voice, voice_style, max_retries, 
                                   safe_voice_styles, risky_styles):
    """
    Menggunakan API sederhana tanpa token (metode lama) - TIDAK DIGUNAKAN LAGI.
    Fungsi ini disimpan untuk kompatibilitas tapi tidak akan dipanggil.
    """
    print("WARNING: Simple API method called but not used - using token method instead")
    return None

def generate_audio_from_text(text_input, bahasa="id-ID", voice="nova", voice_style="friendly", 
                           max_retries_override=2, auth_token=None):
    """
    Fungsi wrapper untuk kompatibilitas dengan kode yang sudah ada.
    Parameter auth_token diabaikan karena token sudah hardcoded.
    """
    # Abaikan parameter auth_token dan selalu gunakan token hardcoded
    return generate_audio_from_text_with_token(
        text_input=text_input,
        bahasa=bahasa,
        voice=voice,
        voice_style=voice_style,
        max_retries_override=max_retries_override
    )
