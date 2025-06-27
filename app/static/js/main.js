document.addEventListener('DOMContentLoaded', function() {
    // --- Referensi Elemen Global ---
    const videoForm = document.getElementById('videoForm');
    const submitButton = document.getElementById('submitButton');
    const progressArea = document.getElementById('progressArea');
    const statusMessages = document.getElementById('statusMessages');
    const loader = document.getElementById('loader');
    const resultsArea = document.getElementById('resultsArea');
    const resultMessage = document.getElementById('resultMessage');
    const videoPlayerContainer = document.getElementById('videoPlayerContainer');
    const storyPreview = document.getElementById('storyPreview');
    const reportDisplayArea = document.getElementById('reportDisplayArea');
    
    const DEFAULT_ASPECT_RATIO_JS = '16:9';

    console.log("main.js loaded - Form submission handler ready");

    if (videoForm) {
        videoForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            console.log("Form submitted - starting video generation process");

            // --- Reset UI untuk proses baru ---
            submitButton.disabled = true;
            loader.style.display = 'block';
            progressArea.style.display = 'block';
            statusMessages.textContent = 'Memulai proses...';
            resultsArea.style.display = 'none';
            reportDisplayArea.style.display = 'none';
            reportDisplayArea.innerHTML = '';
            
            // Bersihkan video container sepenuhnya untuk menghindari bentrok
            videoPlayerContainer.innerHTML = '';
            videoPlayerContainer.style.display = 'none';
            storyPreview.textContent = '';
            storyPreview.style.display = 'none';

            const formDataForBackend = new FormData(videoForm); 

            try {
                // --- FASE 1: GENERASI NARASI, AUDIO, & PROMPT GAMBAR ---
                statusMessages.textContent = `Fase 1/2: Menghubungi server untuk memproses narasi, audio, dan prompt gambar...`;
                console.log("Phase 1: Sending request to /generate_media_prompts");
                
                const phase1Response = await fetch('/generate_media_prompts', {
                    method: 'POST',
                    body: formDataForBackend
                });
                const phase1Result = await phase1Response.json();

                console.log("Phase 1 response:", phase1Result);

                // Tampilkan laporan dari Fase 1 jika ada
                if (phase1Result.report || phase1Result.report_phase1) {
                    const reportData = phase1Result.report || phase1Result.report_phase1;
                    displayReport(reportData, "Laporan Tahap Awal (Audio & Prompt)");
                }

                if (!phase1Response.ok || phase1Result.error) {
                    throw new Error(phase1Result.error || `Gagal di Fase 1 (Server).`);
                }

                statusMessages.textContent = 'Fase 1 selesai. Menyiapkan data untuk pembuatan video...';
                
                // --- FASE 2: MERANGKAI VIDEO ---
                const segmentsToProcess = phase1Result.segments_to_process;
                const fullStoryTextPreview = phase1Result.full_story_text_preview;
                
                console.log("Segments to process:", segmentsToProcess?.length || 0);

                if (!segmentsToProcess || segmentsToProcess.length === 0) {
                    throw new Error('Tidak ada segmen yang valid untuk diproses menjadi video.');
                }

                const effectSettings = {
                    enabled: formDataForBackend.get('effects_enabled') === 'true',
                    fade_prob: parseInt(formDataForBackend.get('fade_probability')) / 100.0,
                    zoom_in_prob: parseInt(formDataForBackend.get('zoom_in_probability')),
                    zoom_out_prob: parseInt(formDataForBackend.get('zoom_out_probability')),
                    static_prob: parseInt(formDataForBackend.get('static_probability'))
                };

                const pollinationsImageModel = formDataForBackend.get('image_model'); 
                const imageAspectRatio = document.getElementById('aspect_ratio')?.value || DEFAULT_ASPECT_RATIO_JS;
                const imageMaxRetries = formDataForBackend.get('image_max_retries');
                
                // TAMBAHAN BARU: Ambil setting GPU acceleration
                const gpuAccelerationEnabled = formDataForBackend.get('gpu_acceleration_enabled') === 'true';
                console.log("GPU Acceleration enabled:", gpuAccelerationEnabled);

                statusMessages.textContent = `Fase 2/2: Mengirim ${segmentsToProcess.length} segmen ke server untuk dirangkai menjadi video...`;
                console.log("Phase 2: Sending request to /create_final_video");
                
                const phase2Response = await fetch("/create_final_video", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        story_segments_with_images: segmentsToProcess,
                        effect_settings: effectSettings,
                        pollinations_image_model: pollinationsImageModel,
                        aspect_ratio: imageAspectRatio, 
                        image_max_retries: imageMaxRetries,
                        gpu_acceleration_enabled: gpuAccelerationEnabled // TAMBAHAN BARU
                    })
                });
                const phase2Result = await phase2Response.json();

                console.log("Phase 2 response:", phase2Result);

                // Gabungkan dan tampilkan laporan dari Fase 2
                if (phase2Result.report) {
                    displayReport(phase2Result.report, "Laporan Tahap Akhir (Gambar & Video)");
                }

                if (phase2Response.ok && phase2Result.video_url) {
                    console.log("Video creation successful! URL:", phase2Result.video_url);
                    
                    // Sembunyikan loader dan progress area
                    loader.style.display = 'none';
                    progressArea.style.display = 'none';
                    
                    // Update status dan result message
                    statusMessages.textContent = 'Proses selesai! Video berhasil dibuat!';
                    resultMessage.textContent = phase2Result.message || 'Video telah selesai diproses.';
                    
                    // Panggil fungsi yang sudah diperbaiki untuk menampilkan video
                    createAndDisplayVideo(phase2Result.video_url);
                    
                    console.log("Video element created and displayed successfully");

                    // Tampilkan story preview jika ada
                    if (fullStoryTextPreview) {
                        storyPreview.textContent = fullStoryTextPreview;
                        storyPreview.style.display = 'block';
                        console.log("Story preview displayed");
                    }
                    
                    // Tampilkan area hasil
                    resultsArea.style.display = 'block';
                    console.log("Results area displayed");

                } else {
                    throw new Error(phase2Result.error || 'Terjadi kesalahan tidak diketahui saat merangkai video.');
                }

            } catch (error) {
                console.error('Error saat proses utama:', error);
                
                // Sembunyikan loader
                loader.style.display = 'none';
                
                // Update status dengan error
                statusMessages.textContent = `Error: ${error.message}. Periksa konsol untuk detail.`;
                resultMessage.textContent = `Gagal memproses: ${error.message}`;
                
                // Tampilkan area progress dan hasil untuk menunjukkan error
                progressArea.style.display = 'block';
                resultsArea.style.display = 'block';
            } finally {
                // Re-enable submit button
                submitButton.disabled = false;
                console.log("Form submission process completed");
            }
        });
    } else {
        console.error("Video form not found!");
    }

    /**
     * **FIXED**: Fungsi untuk membuat dan menampilkan video. 
     * Menggunakan elemen <source> untuk keandalan yang lebih baik.
     * @param {string} videoUrl - URL dari video yang akan ditampilkan.
     */
    function createAndDisplayVideo(videoUrl) {
        try {
            console.log("Creating video element for URL:", videoUrl);
            
            // Pastikan container bersih sebelum menambahkan video baru
            videoPlayerContainer.innerHTML = '';
            
            // Buat elemen video utama
            const videoElement = document.createElement('video');
            videoElement.controls = true; // Tampilkan kontrol video
            videoElement.style.width = '100%';
            videoElement.style.borderRadius = '8px';
            videoElement.style.backgroundColor = '#000';

            // Buat elemen source, ini cara yang lebih direkomendasikan
            const sourceElement = document.createElement('source');
            sourceElement.src = videoUrl;
            sourceElement.type = 'video/mp4';

            // Tambahkan event listener untuk error pada source
            sourceElement.addEventListener('error', function(e) {
                 console.error("Video source error:", e);
                 resultMessage.textContent = `Error memuat sumber video. Coba unduh manual.`;
            });
            
            // Tambahkan source ke dalam video element
            videoElement.appendChild(sourceElement);

            // Tambahkan pesan fallback jika browser tidak mendukung video tag
            const fallbackText = document.createTextNode('Browser Anda tidak mendukung tag video.');
            videoElement.appendChild(fallbackText);
            
            // Tambahkan video element yang sudah lengkap ke dalam container
            videoPlayerContainer.appendChild(videoElement);
            videoPlayerContainer.style.display = 'block'; // Tampilkan container
            
            console.log("Video element with source tag added and displayed.");
            
        } catch (error) {
            console.error("Error creating video element:", error);
            videoPlayerContainer.innerHTML = `
                <div class="video-error" style="padding: 20px; text-align: center; color: #e74c3c;">
                    <p>Gagal menampilkan video player. Silakan coba unduh langsung.</p>
                    <p><a href="${videoUrl}" target="_blank" style="color: #00c2cb;">Unduh Video</a></p>
                </div>
            `;
            videoPlayerContainer.style.display = 'block';
        }
    }

    /**
     * Menampilkan data laporan di UI. Bisa dipanggil beberapa kali untuk menambah laporan.
     * @param {object} reportData - Objek berisi data laporan.
     * @param {string} title - Judul untuk bagian laporan ini.
     */
    function displayReport(reportData, title) {
        if (!reportDisplayArea || !reportData || Object.keys(reportData).length === 0) {
            console.log("No report data to display");
            return;
        }

        console.log("Displaying report:", title, reportData);
        reportDisplayArea.style.display = 'block';
        
        let reportHTML = '';
        // Tambahkan judul hanya jika belum ada, atau jika ada judul baru
        if (!reportDisplayArea.innerHTML.includes('<h3>') || title) {
            reportHTML += `<h3>${title || 'Laporan Generasi Media:'}</h3>`;
        }
        
        reportHTML += '<ul>';
        for (const key in reportData) {
            if (reportData.hasOwnProperty(key)) {
                const readableKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                reportHTML += `<li><strong>${readableKey}:</strong> ${reportData[key]}</li>`;
            }
        }
        reportHTML += '</ul>';
        
        // Tambahkan konten baru ke laporan yang sudah ada
        reportDisplayArea.innerHTML += reportHTML;
    }
});