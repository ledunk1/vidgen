"""
Script untuk menulis ulang teks yang melanggar kebijakan konten TTS
dengan fokus pada keamanan dan konsistensi narasi.
"""

import re
from typing import Optional, Dict, List

class TTSContentPolicyRewriter:
    """
    Kelas untuk menulis ulang teks agar aman untuk TTS dan mematuhi kebijakan konten.
    """
    
    def __init__(self):
        # Daftar kata-kata bermasalah dan penggantinya
        self.problematic_words = {
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
            'duka': 'sedih'
        }
        
        # Frasa bermasalah yang perlu diganti
        self.problematic_phrases = {
            'darah mengalir': 'cairan merah menetes',
            'tubuh berlumuran darah': 'tubuh tertutup cairan merah',
            'jeritan mengerikan': 'teriakan mengejutkan',
            'suasana mencekam': 'suasana menegangkan',
            'kegelapan pekat': 'tempat yang sangat gelap',
            'hantu gentayangan': 'sosok misterius berkeliaran',
            'roh jahat': 'entitas gelap',
            'kutukan kuno': 'mantra kuno',
            'mati mengenaskan': 'pingsan dengan cara yang menyedihkan'
        }

    def sanitize_text_for_tts(self, text: str) -> str:
        """
        Membersihkan teks dari kata-kata yang mungkin memicu kebijakan konten TTS.
        
        Args:
            text (str): Teks asli yang akan dibersihkan
            
        Returns:
            str: Teks yang sudah dibersihkan dan aman untuk TTS
        """
        if not text or not text.strip():
            return text
            
        sanitized_text = text
        
        # 1. Ganti frasa bermasalah terlebih dahulu (lebih spesifik)
        for problematic_phrase, replacement in self.problematic_phrases.items():
            pattern = r'\b' + re.escape(problematic_phrase) + r'\b'
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
        
        # 2. Ganti kata-kata problematik
        for problematic, replacement in self.problematic_words.items():
            # Gunakan regex untuk mengganti kata dengan mempertimbangkan batas kata
            pattern = r'\b' + re.escape(problematic) + r'\b'
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
        
        # 3. Bersihkan karakter khusus yang mungkin bermasalah
        sanitized_text = re.sub(r'[^\w\s\.,!?;:\-\(\)]', ' ', sanitized_text)
        
        # 4. Bersihkan spasi berlebih
        sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
        
        return sanitized_text

    def rewrite_with_ai_provider(self, 
                                original_text: str, 
                                ai_provider: str, 
                                language: str = "Indonesia",
                                gemini_handler=None,
                                pollinations_text_handler=None,
                                provider_data: Dict = None) -> Optional[str]:
        """
        Menulis ulang teks menggunakan provider AI yang dipilih dengan fokus TTS safety.
        
        Args:
            original_text (str): Teks asli yang perlu ditulis ulang
            ai_provider (str): Provider AI ('gemini' atau 'pollinations')
            language (str): Bahasa target
            gemini_handler: Module handler untuk Gemini
            pollinations_text_handler: Module handler untuk Pollinations
            provider_data (Dict): Data konfigurasi provider (API key, model, dll)
            
        Returns:
            Optional[str]: Teks yang sudah ditulis ulang atau None jika gagal
        """
        if not original_text or not original_text.strip():
            return original_text
            
        # Prompt yang sangat spesifik untuk TTS content policy dengan referensi Azure OpenAI
        tts_safe_instruction = (
            f"Tulis ulang teks berikut agar SANGAT AMAN untuk text-to-speech dan mematuhi semua kebijakan konten "
            f"yang aman dan sesuai kebijakan Azure OpenAI. "
            f"Hindari kata-kata yang berhubungan dengan: kekerasan, horor, supernatural, kematian, darah, hantu, "
            f"setan, kutukan, penderitaan, atau hal-hal yang menakutkan. "
            f"Ganti dengan kata-kata yang lebih netral dan aman. "
            f"Pertahankan alur cerita dan makna inti, tapi buat versi yang sangat ramah untuk semua umur "
            f"dan sepenuhnya mematuhi standar keamanan konten Azure OpenAI. "
            f"Teks harus dalam bahasa {language}. "
            f"Pastikan hasil akhir benar-benar aman, positif, dan tidak mengandung konten yang dapat "
            f"melanggar kebijakan konten platform AI manapun. "
            f"Hanya berikan teks hasil penulisan ulang tanpa tambahan komentar."
        )
        
        rewritten_text = None
        
        if ai_provider == 'gemini' and gemini_handler:
            try:
                gemini_api_key = provider_data.get('gemini_api_key') if provider_data else None
                if gemini_api_key and gemini_handler.configure_gemini(gemini_api_key):
                    selected_model = provider_data.get('gemini_model', 'gemini-2.0-flash') if provider_data else 'gemini-2.0-flash'
                    
                    # Gunakan prompt khusus untuk TTS safety dengan referensi Azure OpenAI
                    safe_prompt = f"{tts_safe_instruction}\n\nTeks asli:\n{original_text}"
                    
                    rewritten_text = gemini_handler.generate_text_content(
                        selected_model, safe_prompt, temperature=0.3, max_output_tokens=1024
                    )
                    
                    if rewritten_text:
                        print(f"  Teks berhasil ditulis ulang oleh Gemini untuk TTS safety dengan standar Azure OpenAI.")
                    else:
                        print(f"  Gagal mendapatkan hasil penulisan ulang dari Gemini.")
                else:
                    print(f"  Peringatan: Gemini API Key tidak tersedia untuk rewrite teks.")
            except Exception as e:
                print(f"  Error saat meminta penulisan ulang teks ke Gemini: {e}")
        
        elif ai_provider == 'pollinations' and pollinations_text_handler:
            try:
                selected_model = provider_data.get('pollinations_text_model', 'openai') if provider_data else 'openai'
                
                main_prompt = f"Teks yang perlu ditulis ulang untuk TTS dengan standar Azure OpenAI: {original_text}"
                
                rewritten_text = pollinations_text_handler.generate_text_pollinations(
                    main_prompt=main_prompt,
                    model=selected_model,
                    system_prompt=tts_safe_instruction,
                    private=True,
                    temperature=0.3
                )
                
                if rewritten_text and isinstance(rewritten_text, str):
                    print(f"  Teks berhasil ditulis ulang oleh Pollinations untuk TTS safety dengan standar Azure OpenAI.")
                else:
                    print(f"  Gagal mendapatkan hasil penulisan ulang dari Pollinations.")
                    rewritten_text = None
            except Exception as e:
                print(f"  Error saat meminta penulisan ulang teks ke Pollinations: {e}")
        
        else:
            print(f"  Provider AI '{ai_provider}' tidak mendukung rewrite teks untuk kebijakan konten.")
        
        return rewritten_text

    def comprehensive_rewrite(self, 
                            original_text: str, 
                            ai_provider: str = None,
                            language: str = "Indonesia",
                            **kwargs) -> str:
        """
        Melakukan penulisan ulang komprehensif dengan kombinasi sanitasi dan AI.
        
        Args:
            original_text (str): Teks asli
            ai_provider (str): Provider AI untuk rewrite lanjutan
            language (str): Bahasa target
            **kwargs: Parameter tambahan untuk AI provider
            
        Returns:
            str: Teks yang sudah ditulis ulang secara komprehensif
        """
        if not original_text or not original_text.strip():
            return original_text
        
        # Langkah 1: Sanitasi dasar dengan regex
        sanitized_text = self.sanitize_text_for_tts(original_text)
        print(f"Sanitasi dasar selesai. Panjang: {len(original_text)} -> {len(sanitized_text)}")
        
        # Langkah 2: Jika ada AI provider, lakukan rewrite lanjutan
        if ai_provider and ai_provider in ['gemini', 'pollinations']:
            ai_rewritten = self.rewrite_with_ai_provider(
                sanitized_text, ai_provider, language, **kwargs
            )
            if ai_rewritten and ai_rewritten.strip():
                final_text = ai_rewritten.strip()
                print(f"AI rewrite berhasil dengan standar Azure OpenAI. Panjang akhir: {len(final_text)}")
                return final_text
            else:
                print(f"AI rewrite gagal, menggunakan hasil sanitasi dasar.")
        
        return sanitized_text

# Fungsi utilitas untuk integrasi mudah
def rewrite_text_for_tts_safety(text: str, 
                               ai_provider: str = None, 
                               language: str = "Indonesia",
                               **kwargs) -> str:
    """
    Fungsi utilitas untuk menulis ulang teks agar aman untuk TTS dan sesuai kebijakan Azure OpenAI.
    
    Args:
        text (str): Teks yang akan ditulis ulang
        ai_provider (str): Provider AI ('gemini' atau 'pollinations')
        language (str): Bahasa target
        **kwargs: Parameter tambahan untuk AI provider
        
    Returns:
        str: Teks yang sudah aman untuk TTS dan mematuhi kebijakan Azure OpenAI
    """
    rewriter = TTSContentPolicyRewriter()
    return rewriter.comprehensive_rewrite(text, ai_provider, language, **kwargs)

# Contoh penggunaan
if __name__ == "__main__":
    # Test dengan teks bermasalah
    test_text = """
    Hantu mengerikan itu menyerang dengan brutal, darah mengalir dari tubuh korban yang tersiksa. 
    Jeritan mengerikan memecah keheningan malam yang mencekam. Mayat berlumuran darah tergeletak 
    di lantai yang kelam, sementara roh jahat terus menghantui tempat terkutuk ini.
    """
    
    rewriter = TTSContentPolicyRewriter()
    
    print("Teks Asli:")
    print(test_text)
    print("\n" + "="*50 + "\n")
    
    # Test sanitasi dasar
    sanitized = rewriter.sanitize_text_for_tts(test_text)
    print("Hasil Sanitasi Dasar:")
    print(sanitized)
    print("\n" + "="*50 + "\n")
    
    # Test comprehensive rewrite (tanpa AI)
    comprehensive = rewriter.comprehensive_rewrite(test_text)
    print("Hasil Comprehensive Rewrite dengan Standar Azure OpenAI:")
    print(comprehensive)