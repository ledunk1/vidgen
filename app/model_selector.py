from app.utils import (
    AVAILABLE_GEMINI_MODELS, DEFAULT_GEMINI_MODEL,
    POLLINATIONS_TEXT_MODELS, DEFAULT_POLLINATIONS_TEXT_MODEL,
    PUTER_AI_CHAT_MODELS, DEFAULT_PUTER_AI_CHAT_MODEL
)

def get_available_models_for_provider(ai_provider: str) -> dict:
    """
    Mengembalikan model yang tersedia untuk provider AI tertentu.
    """
    if ai_provider == 'gemini':
        return {
            'models': AVAILABLE_GEMINI_MODELS,
            'default': DEFAULT_GEMINI_MODEL,
            'field_name': 'gemini_model'
        }
    elif ai_provider == 'pollinations':
        return {
            'models': POLLINATIONS_TEXT_MODELS,
            'default': DEFAULT_POLLINATIONS_TEXT_MODEL,
            'field_name': 'pollinations_text_model'
        }
    elif ai_provider == 'puter_ai_chat':
        return {
            'models': PUTER_AI_CHAT_MODELS,
            'default': DEFAULT_PUTER_AI_CHAT_MODEL,
            'field_name': 'puter_ai_chat_model'
        }
    else:
        return {
            'models': [],
            'default': None,
            'field_name': None
        }

def should_show_model_selection(ai_provider: str, narrative_source: str) -> bool:
    """
    Menentukan apakah pilihan model harus ditampilkan berdasarkan provider dan sumber narasi.
    """
    # Untuk sumber file, selalu tampilkan pilihan model
    if narrative_source == 'file':
        return ai_provider in ['gemini', 'pollinations', 'puter_ai_chat']
    
    # Untuk sumber prompt, tampilkan sesuai provider
    if narrative_source == 'prompt':
        return ai_provider in ['gemini', 'pollinations', 'puter_ai_chat']
    
    return False

def get_model_selection_visibility_rules() -> dict:
    """
    Mengembalikan aturan visibilitas untuk setiap section model.
    """
    return {
        'gemini_model_selection_section': {
            'show_when': {
                'ai_provider': 'gemini',
                'narrative_source': ['prompt', 'file']
            }
        },
        'pollinations_model_selection_section': {
            'show_when': {
                'ai_provider': 'pollinations', 
                'narrative_source': ['prompt', 'file']
            }
        },
        'puter_ai_chat_model_section': {
            'show_when': {
                'ai_provider': 'puter_ai_chat',
                'narrative_source': ['prompt', 'file']
            }
        }
    }