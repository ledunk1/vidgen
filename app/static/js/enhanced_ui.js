// Enhanced UI untuk menangani model selection yang lebih baik
document.addEventListener('DOMContentLoaded', function() {
    console.log("enhanced_ui.js loaded - Model Selection Enhancement");

    // Update fungsi existing untuk menangani model selection yang lebih baik
    const originalUpdateFormVisibility = window.updateFormVisibilityBasedOnSelections;
    
    window.updateFormVisibilityBasedOnSelections = function() {
        // Panggil fungsi original terlebih dahulu
        if (originalUpdateFormVisibility) {
            originalUpdateFormVisibility();
        }
        
        // Enhancement: Tampilkan model selection untuk file source
        const narrativeSourceSelect = document.getElementById('narrative_source_select');
        const aiProviderSelect = document.getElementById('ai_provider_select');
        
        if (!narrativeSourceSelect || !aiProviderSelect) {
            return;
        }
        
        const selectedNarrativeSource = narrativeSourceSelect.value;
        const selectedAiProvider = aiProviderSelect.value;
        
        // Model selection sections
        const geminiModelSection = document.getElementById('gemini_model_selection_section');
        const pollinationsModelSection = document.getElementById('pollinations_model_selection_section');
        const puterAiModelSection = document.getElementById('puter_ai_chat_model_section');
        
        // Enhanced logic: Show model selection for file source too
        if (selectedNarrativeSource === 'file') {
            console.log("File source selected - showing appropriate model selection");
            
            // Show model selection based on AI provider for file source
            if (geminiModelSection) {
                const shouldShowGemini = (selectedAiProvider === 'gemini');
                geminiModelSection.classList.toggle('hidden-input', !shouldShowGemini);
                const geminiModelInput = document.getElementById('gemini_model');
                if (geminiModelInput) {
                    geminiModelInput.required = shouldShowGemini;
                }
            }
            
            if (pollinationsModelSection) {
                const shouldShowPollinations = (selectedAiProvider === 'pollinations');
                pollinationsModelSection.classList.toggle('hidden-input', !shouldShowPollinations);
                const pollinationsModelInput = document.getElementById('pollinations_text_model');
                if (pollinationsModelInput) {
                    pollinationsModelInput.required = shouldShowPollinations;
                }
            }
            
            if (puterAiModelSection) {
                const shouldShowPuterAi = (selectedAiProvider === 'puter_ai_chat');
                puterAiModelSection.classList.toggle('hidden-input', !shouldShowPuterAi);
                const puterAiModelInput = document.getElementById('puter_ai_chat_model');
                if (puterAiModelInput) {
                    puterAiModelInput.required = shouldShowPuterAi;
                }
            }
            
            // Show API key section for file source too
            const geminiApiKeySection = document.getElementById('gemini_api_key_section');
            if (geminiApiKeySection && selectedAiProvider === 'gemini') {
                geminiApiKeySection.classList.remove('hidden-input');
                const geminiApiKeyInput = document.getElementById('gemini_api_key');
                if (geminiApiKeyInput) {
                    geminiApiKeyInput.required = true;
                }
            }
        }
        
        console.log("Enhanced model selection visibility updated");
    };
    
    // **FIXED**: Hapus blok kode yang menyebabkan duplikasi elemen.
    // Elemen untuk "Enhanced Processing" sudah ada secara statis di index.html,
    // jadi tidak perlu dibuat lagi dengan JavaScript.
    
    // Enhanced form submission handling
    const originalFormSubmit = document.getElementById('videoForm');
    if (originalFormSubmit) {
        originalFormSubmit.addEventListener('submit', function(event) {
            const useEnhancedProcessing = document.getElementById('use_enhanced_processing');
            
            if (useEnhancedProcessing && useEnhancedProcessing.checked) {
                console.log("Enhanced processing selected - will use sentence-level logic");
                
                // You can add additional validation or processing here
                // For now, we'll let the form submit normally but the backend
                // can check for the enhanced processing flag
            }
        });
    }
});

// Function to toggle enhanced processing options
window.toggleEnhancedProcessing = function() {
    const enhancedCheckbox = document.getElementById('use_enhanced_processing');
    const enhancedOptions = document.getElementById('enhanced_processing_options');
    
    if (enhancedCheckbox && enhancedOptions) {
        enhancedOptions.style.display = enhancedCheckbox.checked ? 'block' : 'none';
    }
};
