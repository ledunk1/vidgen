// app/static/js/show_conf_ai.js
console.log("show_conf_ai.js Parsing - vEnhancedModelSelection");

// --- Referensi Elemen Form Utama ---
let narrativeSourceSelect, promptInputSection, fileUploadSection, aiProviderSelect,
    geminiApiKeySection, geminiModelSelectionSection, pollinationsModelSelectionSection,
    puterAiChatModelSection, // Dikembalikan
    storyPromptTextarea, narrativeFileInput, numPartsInput,
    narrativeExpertiseSelect, narrativeToneSelect, narrativeFormatSelect,
    narrativeLanguageSelect, promptTemplateSelect, promptTemplateIdSection, styleOptionsSection,
    pollinationsImageModelSection, 
    imageAspectRatioSection,
    narrativeSourcePuterAiInfo, // Info untuk Puter AI
    imagePromptTemplateIdSelectContainer; // Kontainer untuk template prompt gambar

// --- Fungsi untuk Mengontrol Visibilitas Form ---
window.updateFormVisibilityBasedOnSelections = function() {
    console.log("DEBUG SHOW_CONF_AI: updateFormVisibilityBasedOnSelections CALLED");

    // Ambil referensi elemen
    narrativeSourceSelect = narrativeSourceSelect || document.getElementById('narrative_source_select');
    aiProviderSelect = aiProviderSelect || document.getElementById('ai_provider_select');
    promptInputSection = promptInputSection || document.getElementById('prompt_input_section');
    fileUploadSection = fileUploadSection || document.getElementById('file_upload_section');
    geminiApiKeySection = geminiApiKeySection || document.getElementById('gemini_api_key_section');
    geminiModelSelectionSection = geminiModelSelectionSection || document.getElementById('gemini_model_selection_section');
    pollinationsModelSelectionSection = pollinationsModelSelectionSection || document.getElementById('pollinations_model_selection_section');
    puterAiChatModelSection = puterAiChatModelSection || document.getElementById('puter_ai_chat_model_section'); // Dikembalikan
    styleOptionsSection = styleOptionsSection || document.getElementById('style_options_section');
    promptTemplateIdSection = promptTemplateIdSection || document.getElementById('prompt_template_id_section'); // Untuk template narasi
    storyPromptTextarea = storyPromptTextarea || document.getElementById('story_prompt');
    numPartsInput = numPartsInput || document.getElementById('num_parts');
    promptTemplateSelect = promptTemplateSelect || document.getElementById('prompt_template_id'); // Untuk template narasi
    narrativeExpertiseSelect = narrativeExpertiseSelect || document.getElementById('narrative_expertise');
    narrativeToneSelect = narrativeToneSelect || document.getElementById('narrative_tone');
    narrativeFormatSelect = narrativeFormatSelect || document.getElementById('narrative_format');
    narrativeLanguageSelect = narrativeLanguageSelect || document.getElementById('narrative_language');
    narrativeFileInput = narrativeFileInput || document.getElementById('narrative_file');
    narrativeSourcePuterAiInfo = narrativeSourcePuterAiInfo || document.getElementById('narrative_source_puter_ai_info');
    imagePromptTemplateIdSelectContainer = imagePromptTemplateIdSelectContainer || document.getElementById('image_prompt_template_id')?.closest('.form-group');


    pollinationsImageModelSection = pollinationsImageModelSection || document.getElementById('pollinations_image_model_section');
    imageAspectRatioSection = imageAspectRatioSection || document.getElementById('image_aspect_ratio_section');

    if (!narrativeSourceSelect || !aiProviderSelect) {
        console.warn("DEBUG SHOW_CONF_AI: narrativeSourceSelect atau aiProviderSelect TIDAK DITEMUKAN.");
        return;
    }
    console.log("DEBUG SHOW_CONF_AI: aiProviderSelect element:", aiProviderSelect);
    console.log("DEBUG SHOW_CONF_AI: puterAiChatModelSection element:", puterAiChatModelSection);

    const selectedAiProvider = aiProviderSelect.value;
    let selectedNarrativeSource = narrativeSourceSelect.value; // Bisa diubah jika Puter AI dipilih

    console.log("DEBUG SHOW_CONF_AI: Initial selectedNarrativeSource =", selectedNarrativeSource);
    console.log("DEBUG SHOW_CONF_AI: selectedAiProvider =", selectedAiProvider);

    // Logika khusus jika Puter AI dipilih
    if (selectedAiProvider === 'puter_ai_chat') {
        if (narrativeSourceSelect.value === 'file') {
            narrativeSourceSelect.value = 'prompt'; // Paksa ke prompt
            console.log("DEBUG SHOW_CONF_AI: Puter AI dipilih, Sumber Narasi diubah ke 'prompt'.");
            // Picu event change agar UI lain yang bergantung pada narrativeSourceSelect juga update
            narrativeSourceSelect.dispatchEvent(new Event('change')); 
        }
        selectedNarrativeSource = 'prompt'; // Pastikan variabel JS juga update
        if (narrativeSourcePuterAiInfo) narrativeSourcePuterAiInfo.classList.remove('hidden-input');
        // Nonaktifkan opsi file jika Puter AI dipilih
        const fileOption = narrativeSourceSelect.querySelector('option[value="file"]');
        if (fileOption) fileOption.disabled = true;

    } else {
        if (narrativeSourcePuterAiInfo) narrativeSourcePuterAiInfo.classList.add('hidden-input');
        // Aktifkan kembali opsi file jika provider lain dipilih
        const fileOption = narrativeSourceSelect.querySelector('option[value="file"]');
        if (fileOption) fileOption.disabled = false;
    }
    
    const isPromptNarrativeSource = (selectedNarrativeSource === 'prompt');
    const isFileNarrativeSource = (selectedNarrativeSource === 'file');
    const aiProviderGroup = aiProviderSelect.closest('.form-group');

    if (promptInputSection) promptInputSection.classList.toggle('hidden-input', !isPromptNarrativeSource);
    if (fileUploadSection) fileUploadSection.classList.toggle('hidden-input', isPromptNarrativeSource || selectedAiProvider === 'puter_ai_chat');
    
    if (aiProviderGroup) aiProviderGroup.classList.remove('hidden-input'); 
    
    // PERBAIKAN UTAMA: Visibilitas untuk penyedia AI Narasi - tampilkan untuk SEMUA source yang valid
    const shouldShowGeminiOptions = (selectedAiProvider === 'gemini') && (isPromptNarrativeSource || isFileNarrativeSource);
    const shouldShowPollinationsOptions = (selectedAiProvider === 'pollinations') && (isPromptNarrativeSource || isFileNarrativeSource);
    const shouldShowPuterAiOptions = (selectedAiProvider === 'puter_ai_chat') && isPromptNarrativeSource; // Puter AI hanya untuk prompt
    
    console.log("DEBUG SHOW_CONF_AI: shouldShowGeminiOptions =", shouldShowGeminiOptions);
    console.log("DEBUG SHOW_CONF_AI: shouldShowPollinationsOptions =", shouldShowPollinationsOptions);
    console.log("DEBUG SHOW_CONF_AI: shouldShowPuterAiOptions =", shouldShowPuterAiOptions);
    
    // PERBAIKAN: Tampilkan API Key section untuk file source juga
    if (geminiApiKeySection) {
        geminiApiKeySection.classList.toggle('hidden-input', !shouldShowGeminiOptions);
        const geminiApiKeyInput = document.getElementById('gemini_api_key');
        if (geminiApiKeyInput) geminiApiKeyInput.required = shouldShowGeminiOptions;
        console.log("DEBUG SHOW_CONF_AI: geminiApiKeySection hidden =", !shouldShowGeminiOptions);
    }
    
    // PERBAIKAN: Tampilkan Model Selection untuk file source juga
    if (geminiModelSelectionSection) {
        geminiModelSelectionSection.classList.toggle('hidden-input', !shouldShowGeminiOptions);
        const geminiModelInput = document.getElementById('gemini_model');
        if (geminiModelInput) geminiModelInput.required = shouldShowGeminiOptions;
        console.log("DEBUG SHOW_CONF_AI: geminiModelSelectionSection hidden =", !shouldShowGeminiOptions);
    }

    if (pollinationsModelSelectionSection) {
        pollinationsModelSelectionSection.classList.toggle('hidden-input', !shouldShowPollinationsOptions);
        const pollinationsModelInput = document.getElementById('pollinations_text_model');
        if (pollinationsModelInput) pollinationsModelInput.required = shouldShowPollinationsOptions;
        console.log("DEBUG SHOW_CONF_AI: pollinationsModelSelectionSection hidden =", !shouldShowPollinationsOptions);
    }
    
    if (puterAiChatModelSection) {
        puterAiChatModelSection.classList.toggle('hidden-input', !shouldShowPuterAiOptions);
        console.log("DEBUG SHOW_CONF_AI: puterAiChatModelSection hidden =", !shouldShowPuterAiOptions);
        const puterAiModelInput = document.getElementById('puter_ai_chat_model');
        if (puterAiModelInput) {
            puterAiModelInput.required = shouldShowPuterAiOptions;
        }
    } else {
        console.warn("DEBUG SHOW_CONF_AI: puterAiChatModelSection TIDAK DITEMUKAN saat toggle.");
    }
    
    // PERBAIKAN: Hanya sembunyikan style options untuk file source, bukan model selection
    const showPromptSpecificOptions = isPromptNarrativeSource;

    if (styleOptionsSection) styleOptionsSection.classList.toggle('hidden-input', !showPromptSpecificOptions || selectedAiProvider === 'puter_ai_chat');
    
    // Sembunyikan template prompt narasi jika Puter AI dipilih atau file source
    if (promptTemplateIdSection) {
      promptTemplateIdSection.classList.toggle('hidden-input', !showPromptSpecificOptions || selectedAiProvider === 'puter_ai_chat');
    }
    // Sembunyikan template prompt gambar jika Puter AI dipilih (karena Puter AI buat sendiri)
    if (imagePromptTemplateIdSelectContainer) {
        imagePromptTemplateIdSelectContainer.classList.toggle('hidden-input', selectedAiProvider === 'puter_ai_chat');
    }
    
    if (storyPromptTextarea && storyPromptTextarea.closest('.form-group')) {
        storyPromptTextarea.closest('.form-group').classList.toggle('hidden-input', !showPromptSpecificOptions);
    }
    if (numPartsInput && numPartsInput.closest('.form-group')) {
        numPartsInput.closest('.form-group').classList.toggle('hidden-input', !showPromptSpecificOptions);
    }
    const wordCountInputs = document.querySelector('.word-count-inputs');
    if (wordCountInputs && wordCountInputs.closest('.input-option') === promptInputSection) {
         wordCountInputs.classList.toggle('hidden-input', !showPromptSpecificOptions);
    }
    
    // PERBAIKAN: Set required fields berdasarkan source dan provider
    if (promptTemplateSelect) { // Template narasi
        promptTemplateSelect.disabled = !showPromptSpecificOptions || selectedAiProvider === 'puter_ai_chat';
        promptTemplateSelect.required = showPromptSpecificOptions && selectedAiProvider !== 'puter_ai_chat'; 
    }
    
    if (storyPromptTextarea) storyPromptTextarea.required = showPromptSpecificOptions;
    if (narrativeFileInput) narrativeFileInput.required = isFileNarrativeSource && selectedAiProvider !== 'puter_ai_chat'; 
    if (numPartsInput) numPartsInput.required = showPromptSpecificOptions;
    if (document.getElementById('min_words_per_part')) document.getElementById('min_words_per_part').required = showPromptSpecificOptions;
    if (document.getElementById('max_words_per_part')) document.getElementById('max_words_per_part').required = showPromptSpecificOptions;

    if (narrativeExpertiseSelect) narrativeExpertiseSelect.required = showPromptSpecificOptions;
    if (narrativeToneSelect) narrativeToneSelect.required = showPromptSpecificOptions;
    if (narrativeFormatSelect) narrativeFormatSelect.required = showPromptSpecificOptions;
    if (narrativeLanguageSelect) narrativeLanguageSelect.required = showPromptSpecificOptions; 

    if (pollinationsImageModelSection) {
        pollinationsImageModelSection.classList.remove('hidden-input'); 
        const imageModelInput = document.getElementById('image_model');
        if (imageModelInput) {
            imageModelInput.required = true; 
        }
    }

    if (imageAspectRatioSection) {
        imageAspectRatioSection.classList.remove('hidden-input');
    }
    
    console.log("DEBUG SHOW_CONF_AI: updateFormVisibilityBasedOnSelections FINISHED");
    console.log("DEBUG SHOW_CONF_AI: Enhanced model selection logic applied for file source");
}


document.addEventListener('DOMContentLoaded', function() {
    console.log("show_conf_ai.js DOMContentLoaded - Event listeners dipasang.");
    // Inisialisasi semua referensi elemen di sini
    narrativeSourceSelect = document.getElementById('narrative_source_select');
    promptInputSection = document.getElementById('prompt_input_section');
    fileUploadSection = document.getElementById('file_upload_section');
    aiProviderSelect = document.getElementById('ai_provider_select');
    geminiApiKeySection = document.getElementById('gemini_api_key_section');
    geminiModelSelectionSection = document.getElementById('gemini_model_selection_section');
    pollinationsModelSelectionSection = document.getElementById('pollinations_model_selection_section');
    puterAiChatModelSection = document.getElementById('puter_ai_chat_model_section'); 
    storyPromptTextarea = document.getElementById('story_prompt');
    narrativeFileInput = document.getElementById('narrative_file');
    numPartsInput = document.getElementById('num_parts');
    narrativeExpertiseSelect = document.getElementById('narrative_expertise');
    narrativeToneSelect = document.getElementById('narrative_tone');
    narrativeFormatSelect = document.getElementById('narrative_format');
    narrativeLanguageSelect = document.getElementById('narrative_language');
    promptTemplateSelect = document.getElementById('prompt_template_id'); // Untuk template narasi
    promptTemplateIdSection = document.getElementById('prompt_template_id_section');
    styleOptionsSection = document.getElementById('style_options_section');
    narrativeSourcePuterAiInfo = document.getElementById('narrative_source_puter_ai_info');
    imagePromptTemplateIdSelectContainer = document.getElementById('image_prompt_template_id')?.closest('.form-group');

    pollinationsImageModelSection = document.getElementById('pollinations_image_model_section');
    imageAspectRatioSection = document.getElementById('image_aspect_ratio_section');

    if (narrativeSourceSelect) {
        narrativeSourceSelect.addEventListener('change', window.updateFormVisibilityBasedOnSelections);
    }
    if (aiProviderSelect) {
        aiProviderSelect.addEventListener('change', window.updateFormVisibilityBasedOnSelections);
    }
    
    if (typeof window.updateFormVisibilityBasedOnSelections === 'function') {
        console.log("DEBUG SHOW_CONF_AI: Calling updateFormVisibilityBasedOnSelections on DOMContentLoaded");
        window.updateFormVisibilityBasedOnSelections();
    }
    console.log("show_conf_ai.js: Event listener DOMContentLoaded selesai & updateFormVisibilityBasedOnSelections dipanggil.");
});