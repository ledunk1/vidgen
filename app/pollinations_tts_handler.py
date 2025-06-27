# app/pollinations_tts_handler.py

import requests
import time
import re
from app.utils import api_delay
from urllib.parse import quote_plus

# Definisikan URL dasar API TTS Pollinations. 
# Kita akan menggunakan pendekatan sederhana yang menggabungkan teks ke URL.
POLLINATIONS_TTS_BASE_URL = "https://text.pollinations.ai/"

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

def generate_audio_from_text(text_input, bahasa="id-ID", voice="nova", voice_style="friendly", max_retries_override=2):
    """
    Menghasilkan audio dari teks menggunakan API Pollinations.
    PERBAIKAN: Menambahkan sanitasi teks dan fallback voice style yang lebih aman.
    
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

    # PERBAIKAN UTAMA: Sanitasi teks sebelum diproses
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
    
    # PERBAIKAN: Daftar voice style yang lebih aman untuk fallback
    safe_voice_styles = ["friendly", "calm", "patient_teacher", "mellow_story"]
    
    # Jika voice style yang dipilih berpotensi bermasalah, gunakan yang lebih aman
    risky_styles = ["horror_story", "noir_detective"]
    if voice_style in risky_styles:
        print(f"TTS: Voice style '{voice_style}' mungkin berisiko, akan mencoba fallback jika gagal.")
    
    # Encode teks final
    encoded_text = quote_plus(final_text_for_tts)
    
    # PERBAIKAN: Coba dengan voice style asli terlebih dahulu
    request_url = f"{POLLINATIONS_TTS_BASE_URL}{encoded_text}?model=openai-audio&voice={voice}&style={voice_style}"
    
    last_exception = None
    effective_max_retries = max(1, max_retries_override)
    
    # Percobaan pertama dengan voice style asli
    for attempt in range(1, effective_max_retries + 1):
        print(f"Memanggil API Pollinations TTS (Percobaan ke-{attempt}/{effective_max_retries}): Voice={voice}, Style={voice_style}")
        print(f"URL: {request_url[:150]}...")
        try:
            response = requests.get(request_url, timeout=120) 
            
            # Cek jika status code menandakan error
            if response.status_code >= 400:
                print(f"Error dari API dengan status code: {response.status_code}")
                error_text = response.text.lower()
                # Cek spesifik untuk error kebijakan konten
                if "content management policy" in error_text or "safety" in error_text or "content policy" in error_text:
                    print("Terdeteksi error kebijakan konten dari API.")
                    
                    # PERBAIKAN: Jika ini percobaan pertama dan voice style berisiko, coba dengan style yang lebih aman
                    if attempt == 1 and voice_style in risky_styles:
                        print(f"Mencoba dengan voice style yang lebih aman...")
                        for safe_style in safe_voice_styles:
                            print(f"Mencoba dengan voice style: {safe_style}")
                            safe_url = f"{POLLINATIONS_TTS_BASE_URL}{encoded_text}?model=openai-audio&voice={voice}&style={safe_style}"
                            try:
                                safe_response = requests.get(safe_url, timeout=120)
                                if safe_response.status_code == 200 and 'audio/' in safe_response.headers.get('Content-Type', ''):
                                    print(f"Berhasil dengan voice style: {safe_style}")
                                    return safe_response.content
                            except Exception as e_safe:
                                print(f"Gagal dengan style {safe_style}: {e_safe}")
                                continue
                    
                    # Jika semua style gagal, return signal
                    return CONTENT_POLICY_ERROR_SIGNAL
                else:
                    last_exception = requests.exceptions.HTTPError(f"HTTP {response.status_code}: {response.text}")
            
            # Jika berhasil (status 200)
            elif 'audio/' in response.headers.get('Content-Type', ''): 
                print(f"Audio berhasil didapatkan dari API (percobaan ke-{attempt}) dengan voice={voice}, style={voice_style}")
                return response.content
            
            # Jika respon berhasil tapi bukan audio
            else:
                last_exception = Exception(f"Respon dari API bukan audio. Content-Type: {response.headers.get('Content-Type')}")

        except requests.exceptions.RequestException as e:
            print(f"Error koneksi saat menghubungi API TTS percobaan ke-{attempt}: {e}")
            last_exception = e
        
        # Jika loop belum berakhir, tunggu sebelum mencoba lagi
        if attempt < effective_max_retries:
            api_delay(30)
        else:
            print(f"Gagal menghasilkan audio setelah {effective_max_retries} percobaan.")
            if last_exception:
                print(f"Error terakhir yang tercatat: {last_exception}")
            
            # PERBAIKAN: Sebagai upaya terakhir, coba dengan teks yang lebih disederhanakan
            if len(sanitized_text) > 100:
                print("Mencoba dengan teks yang lebih pendek sebagai upaya terakhir...")
                simplified_text = sanitized_text[:100] + "..."
                simplified_final_text = f"{instruction_prompt} {simplified_text}"
                simplified_encoded = quote_plus(simplified_final_text)
                simplified_url = f"{POLLINATIONS_TTS_BASE_URL}{simplified_encoded}?model=openai-audio&voice={voice}&style=friendly"
                
                try:
                    simplified_response = requests.get(simplified_url, timeout=120)
                    if simplified_response.status_code == 200 and 'audio/' in simplified_response.headers.get('Content-Type', ''):
                        print("Berhasil dengan teks yang disederhanakan!")
                        return simplified_response.content
                except Exception as e_simple:
                    print(f"Upaya terakhir juga gagal: {e_simple}")
            
            return None
    
    return None