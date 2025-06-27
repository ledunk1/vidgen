// app/static/js/settings_manager.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("[SettingsManager] DOMContentLoaded - Mulai (Re-integrasi Puter AI + GPU Acceleration).");

    const formId = 'videoForm'; 
    const formElement = document.getElementById(formId);

    if (!formElement) {
        console.error(`[SettingsManager] Form dengan ID '${formId}' tidak ditemukan.`);
        return;
    }

    const fieldsToPersist = [
        'ai_provider_select', 'gemini_api_key', 'narrative_source_select', 
        'prompt_template_id', 'story_prompt', 'num_parts', 
        'min_words_per_part', 'max_words_per_part',
        'gemini_model', 'pollinations_text_model', 
        'puter_ai_chat_model', // Dikembalikan untuk menyimpan pilihan model Puter AI
        'narrative_expertise', 
        'narrative_tone', 'narrative_format', 'narrative_language', 
        'character_description', 'tts_voice', 'tts_voice_style', 'tts_max_retries', 
        'image_model', // Ini untuk Pollinations Image Model
        'aspect_ratio', 'image_max_retries', 
        'images_per_chunk_min', 'images_per_chunk_max', 'effects_enabled', 
        'fade_probability', 'zoom_in_probability', 'zoom_out_probability', 
        'static_probability', 'gpu_acceleration_enabled' // TAMBAHAN BARU: GPU acceleration setting
    ];

    function saveSetting(id, value) {
        try {
            localStorage.setItem(id, value);
        } catch (e) {
            console.error(`[SettingsManager] Error menyimpan pengaturan untuk '${id}':`, e);
        }
    }

    function loadAndApplySetting(id) {
        const element = document.getElementById(id);
        if (!element) {
            // console.warn(`[SettingsManager] Elemen dengan ID '${id}' tidak ditemukan saat memuat.`);
            return; 
        }
        const savedValue = localStorage.getItem(id);
        if (savedValue !== null) {
            if (element.type === 'checkbox') {
                element.checked = (savedValue === 'true');
            } else {
                element.value = savedValue;
            }
            if (element.type === 'range' && element.nextElementSibling && element.nextElementSibling.tagName === 'OUTPUT') {
                element.nextElementSibling.value = element.value + '%';
            }
            // Picu event 'change' agar show_conf_ai.js dapat merespons nilai yang dimuat
            // terutama untuk select elements seperti ai_provider_select
            const eventName = (element.tagName === 'SELECT' || element.type === 'checkbox') ? 'change' : 'input';
            element.dispatchEvent(new Event(eventName, { bubbles: true, cancelable: true }));
        }
    }

    console.log("[SettingsManager] Memulai pemuatan semua pengaturan...");
    fieldsToPersist.forEach(id => {
        loadAndApplySetting(id);
    });
    console.log("[SettingsManager] Selesai memuat semua pengaturan dari localStorage.");

    // Pemanggilan fungsi update UI global setelah semua nilai dimuat dan event awal dipicu.
    // Jeda ini penting agar skrip lain (show_conf_ai.js) sudah siap.
    setTimeout(function() {
        console.log("[SettingsManager] Mencoba memanggil fungsi update UI global setelah jeda...");
        if (typeof window.updateFormVisibilityBasedOnSelections === 'function') {
            console.log("[SettingsManager] Memanggil updateFormVisibilityBasedOnSelections.");
            window.updateFormVisibilityBasedOnSelections();
        } else {
            console.warn("[SettingsManager] Fungsi window.updateFormVisibilityBasedOnSelections TIDAK DITEMUKAN.");
        }
        
        if (typeof window.toggleEffectProbabilities === 'function') { 
            console.log("[SettingsManager] Memanggil toggleEffectProbabilities.");
            window.toggleEffectProbabilities();
        } else {
            console.warn("[SettingsManager] Fungsi window.toggleEffectProbabilities TIDAK DITEMUKAN.");
        }

        if (typeof window.updateTotalMotionDisplay === 'function') { 
            console.log("[SettingsManager] Memanggil updateTotalMotionDisplay.");
            window.updateTotalMotionDisplay();
        } else {
             console.warn("[SettingsManager] Fungsi window.updateTotalMotionDisplay TIDAK DITEMUKAN.");
        }
        console.log("[SettingsManager] Inisialisasi UI setelah load settings selesai.");
    }, 250); // Sedikit menambah jeda untuk memastikan semua skrip lain siap

    fieldsToPersist.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            let eventType = 'input'; 
            if (element.type === 'select-one' || element.type === 'checkbox') {
                eventType = 'change';
            }
            if (element.id === 'gemini_api_key' && element.type === 'password') {
                eventType = 'blur'; 
                 element.addEventListener('paste', () => { 
                    setTimeout(() => saveSetting(element.id, element.value), 50);
                });
            }
            element.addEventListener(eventType, function(event) {
                const currentElement = event.target;
                let valueToSave;
                if (currentElement.type === 'checkbox') {
                    valueToSave = currentElement.checked;
                } else {
                    valueToSave = currentElement.value;
                }
                // Untuk API key, simpan dengan sedikit jeda setelah blur atau paste
                if (currentElement.id === 'gemini_api_key' && currentElement.type === 'password') {
                    setTimeout(() => { 
                        saveSetting(currentElement.id, currentElement.value);
                         console.log(`[SettingsManager] Saved ${currentElement.id} on ${event.type}`);
                    }, 100);
                } else {
                    saveSetting(currentElement.id, valueToSave);
                    // console.log(`[SettingsManager] Saved ${currentElement.id} = ${valueToSave}`);
                }
            });
        }
    });
    console.log("[SettingsManager] Pemasangan event listener untuk penyimpanan selesai.");
});