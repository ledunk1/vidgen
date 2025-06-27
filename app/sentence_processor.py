import re
from typing import List, Tuple
from app.utils import api_delay

def split_paragraph_into_sentences(paragraph_text: str) -> List[str]:
    """
    Memecah paragraf menjadi kalimat-kalimat berdasarkan tanda baca.
    Mengembalikan list kalimat yang sudah dibersihkan.
    """
    if not paragraph_text or not paragraph_text.strip():
        return []
    
    # Pola untuk memecah kalimat berdasarkan tanda baca
    sentence_endings = r'[.!?]+(?:\s|$)'
    
    # Split berdasarkan tanda baca akhir kalimat
    sentences = re.split(sentence_endings, paragraph_text)
    
    # Bersihkan dan filter kalimat kosong
    cleaned_sentences = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned and len(cleaned) > 10:  # Minimal 10 karakter untuk dianggap kalimat valid
            cleaned_sentences.append(cleaned)
    
    return cleaned_sentences

def split_text_into_sentence_chunks(text: str, max_chars_per_chunk: int = 600) -> List[Tuple[str, List[str]]]:
    """
    Memecah teks menjadi paragraf, lalu setiap paragraf dipecah menjadi kalimat.
    Mengembalikan list tuple (paragraph_text, list_of_sentences).
    """
    if not text or not text.strip():
        return []
    
    # Pisahkan menjadi paragraf terlebih dahulu
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    result_chunks = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Jika paragraf terlalu panjang, pecah menjadi chunk yang lebih kecil
        if len(paragraph) > max_chars_per_chunk:
            # Pecah paragraf panjang menjadi beberapa chunk
            words = paragraph.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk + " " + word) <= max_chars_per_chunk:
                    current_chunk += (" " + word) if current_chunk else word
                else:
                    if current_chunk:
                        sentences = split_paragraph_into_sentences(current_chunk)
                        if sentences:
                            result_chunks.append((current_chunk, sentences))
                    current_chunk = word
            
            # Tambahkan chunk terakhir
            if current_chunk:
                sentences = split_paragraph_into_sentences(current_chunk)
                if sentences:
                    result_chunks.append((current_chunk, sentences))
        else:
            # Paragraf tidak terlalu panjang, langsung pecah menjadi kalimat
            sentences = split_paragraph_into_sentences(paragraph)
            if sentences:
                result_chunks.append((paragraph, sentences))
    
    return result_chunks

def create_sentence_level_prompts(
    paragraph_text: str, 
    sentences: List[str], 
    character_description: str = None,
    previous_context: str = None,
    language: str = "Inggris"
) -> List[str]:
    """
    Membuat prompt gambar untuk setiap kalimat dalam paragraf dengan mempertahankan konsistensi.
    """
    if not sentences:
        return []
    
    prompts = []
    
    # Context untuk konsistensi
    context_info = ""
    if character_description:
        context_info += f"Character consistency: {character_description}. "
    if previous_context:
        context_info += f"Previous scene context: {previous_context[:200]}... "
    
    for i, sentence in enumerate(sentences):
        # Buat prompt yang konsisten untuk setiap kalimat
        prompt_parts = []
        
        # Tambahkan konteks karakter jika ada
        if character_description:
            prompt_parts.append(f"Featuring {character_description}")
        
        # Deskripsi utama berdasarkan kalimat
        main_description = f"Scene depicting: {sentence}"
        prompt_parts.append(main_description)
        
        # Tambahkan konteks paragraf untuk konsistensi
        if len(sentences) > 1:
            prompt_parts.append(f"Part of larger scene: {paragraph_text[:150]}...")
        
        # Tambahkan style dan quality indicators
        prompt_parts.append("High quality, detailed, cinematic lighting, professional composition")
        
        # Gabungkan semua bagian prompt
        full_prompt = ", ".join(prompt_parts)
        
        # Pastikan prompt tidak terlalu panjang
        if len(full_prompt) > 500:
            full_prompt = full_prompt[:497] + "..."
        
        prompts.append(full_prompt)
    
    return prompts

def process_sentence_level_media_generation(
    paragraph_chunks: List[Tuple[str, List[str]]],
    ai_provider: str,
    gemini_handler_module,
    pollinations_text_handler_module,
    character_description: str = None,
    language: str = "Inggris",
    template_content: str = None
) -> List[dict]:
    """
    Memproses setiap paragraf dan kalimat untuk menghasilkan prompt gambar yang lebih detail.
    """
    processed_segments = []
    previous_paragraph_context = None
    
    for chunk_index, (paragraph_text, sentences) in enumerate(paragraph_chunks):
        print(f"\nMemproses paragraf ke-{chunk_index + 1} dengan {len(sentences)} kalimat...")
        
        # Generate prompts untuk setiap kalimat dalam paragraf
        sentence_prompts = []
        
        if ai_provider == 'gemini':
            # Gunakan Gemini untuk generate prompts per kalimat
            for sentence_index, sentence in enumerate(sentences):
                print(f"  Membuat prompt untuk kalimat {sentence_index + 1}: {sentence[:50]}...")
                
                # Buat prompt yang lebih spesifik untuk kalimat ini
                sentence_prompt_list = gemini_handler_module.generate_image_prompts_for_paragraph(
                    model_name=None,  # Akan menggunakan default
                    current_chunk_text=sentence,
                    num_prompts_target=1,  # Satu prompt per kalimat
                    character_details=character_description,
                    language=language,
                    previous_chunk_text=previous_paragraph_context,
                    template_content=template_content
                )
                
                if sentence_prompt_list:
                    sentence_prompts.extend(sentence_prompt_list)
                else:
                    # Fallback: buat prompt sederhana jika AI gagal
                    fallback_prompt = create_sentence_level_prompts(
                        paragraph_text, [sentence], character_description, 
                        previous_paragraph_context, language
                    )
                    sentence_prompts.extend(fallback_prompt)
                
                # Delay antar kalimat
                api_delay(4)
        
        elif ai_provider == 'pollinations':
            # Gunakan Pollinations untuk generate prompts per kalimat
            for sentence_index, sentence in enumerate(sentences):
                print(f"  Membuat prompt untuk kalimat {sentence_index + 1}: {sentence[:50]}...")
                
                sentence_prompt_list = pollinations_text_handler_module.generate_image_prompts_via_pollinations(
                    model_name=None,  # Akan menggunakan default
                    current_chunk_text=sentence,
                    num_prompts_target=1,  # Satu prompt per kalimat
                    character_details=character_description,
                    language_of_chunk=language,
                    output_language=language,
                    previous_chunk_text=previous_paragraph_context,
                    template_content=template_content
                )
                
                if sentence_prompt_list:
                    sentence_prompts.extend(sentence_prompt_list)
                else:
                    # Fallback: buat prompt sederhana jika AI gagal
                    fallback_prompt = create_sentence_level_prompts(
                        paragraph_text, [sentence], character_description, 
                        previous_paragraph_context, language
                    )
                    sentence_prompts.extend(fallback_prompt)
                
                # Delay antar kalimat
                api_delay(1)
        
        else:
            # Fallback untuk provider lain atau jika tidak ada AI
            sentence_prompts = create_sentence_level_prompts(
                paragraph_text, sentences, character_description, 
                previous_paragraph_context, language
            )
        
        # Simpan data segmen dengan informasi kalimat
        segment_data = {
            'segment_index': chunk_index,
            'paragraph_text': paragraph_text,
            'sentences': sentences,
            'sentence_count': len(sentences),
            'image_prompts': sentence_prompts,
            'num_images_target': len(sentence_prompts)
        }
        
        processed_segments.append(segment_data)
        
        # Update context untuk paragraf berikutnya
        previous_paragraph_context = paragraph_text
        
        print(f"  Paragraf {chunk_index + 1} selesai: {len(sentence_prompts)} prompt gambar dibuat.")
    
    return processed_segments
