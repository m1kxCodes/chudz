const API_URL = 'http://localhost:8000';
let currentNSFWMode = false;
let currentNSFWModel = 'big_lust';

// ==================== NSFW CONTROLS ====================
document.getElementById('nsfwToggle').addEventListener('change', async (e) => {
    const isEnabled = e.target.checked;
    const nsfwModelSelect = document.getElementById('nsfwModelSelect');
    const nsfwStatus = document.getElementById('nsfwStatus');
    
    if (isEnabled) {
        nsfwModelSelect.style.display = 'block';
        nsfwStatus.textContent = 'Switching to NSFW mode...';
        currentNSFWMode = true;
    } else {
        nsfwModelSelect.style.display = 'none';
        nsfwStatus.textContent = 'Switching to Safe mode...';
        currentNSFWMode = false;
    }
    
    try {
        const response = await fetch(`${API_URL}/switch-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nsfw_mode: isEnabled,
                nsfw_model: currentNSFWModel
            })
        });
        
        if (!response.ok) throw new Error(await getErrorMessage(response, 'Model switch failed'));
        
        const data = await response.json();
        nsfwStatus.textContent = isEnabled ? 'NSFW mode ON' : 'Safe mode';
        nsfwStatus.style.color = isEnabled ? '#ff6b6b' : '#888';
    } catch (error) {
        nsfwStatus.textContent = `Error: ${error.message}`;
        nsfwStatus.style.color = '#ff6b6b';
        console.error(error);
    }
});

document.getElementById('nsfwModelSelect').addEventListener('change', (e) => {
    currentNSFWModel = e.target.value;
});

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Deactivate all tabs
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        // Activate selected tab
        btn.classList.add('active');
        document.getElementById(tabName).classList.add('active');
        
        // Load gallery when switching to gallery tab
        if (tabName === 'gallery') {
            loadGallery();
        }
    });
});

// Initialize device info
async function initializeApp() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();
        
        const deviceInfo = document.getElementById('deviceInfo');
        const modelName = data.model ? data.model.split('/').pop() : 'model';
        const videoModelName = data.video_model ? data.video_model.split('/').pop() : 'video';
        deviceInfo.textContent = data.gpu_available
            ? `GPU: ${data.gpu_name} | ${modelName} | ${videoModelName}`
            : `CPU mode | ${modelName} | ${videoModelName}`;
        
        // Update NSFW status
        const nsfwStatus = document.getElementById('nsfwStatus');
        const nsfwToggle = document.getElementById('nsfwToggle');
        if (data.nsfw_mode) {
            nsfwToggle.checked = true;
            nsfwStatus.textContent = 'NSFW mode ON';
            nsfwStatus.style.color = '#ff6b6b';
            document.getElementById('nsfwModelSelect').style.display = 'block';
            currentNSFWMode = true;
        } else {
            nsfwToggle.checked = false;
            nsfwStatus.textContent = 'Safe mode';
            nsfwStatus.style.color = '#888';
            document.getElementById('nsfwModelSelect').style.display = 'none';
            currentNSFWMode = false;
        }
    } catch (error) {
        console.error('Error fetching device info:', error);
    }
}

// ==================== PROMPT ENHANCER ====================
document.getElementById('enhancePromptBtn').addEventListener('click', async () => {
    await enhancePrompt('prompt', 'negativePrompt', 'stylePreset', 'generateStatus');
});

document.getElementById('enhanceBatchPromptBtn').addEventListener('click', async () => {
    await enhancePrompt('batchPrompt', 'batchNegativePrompt', 'batchStylePreset', 'batchStatus');
});

// ==================== GENERATE IMAGE ====================
document.getElementById('generateBtn').addEventListener('click', async () => {
    const prompt = document.getElementById('prompt').value.trim();
    
    if (!prompt) {
        showStatus('generateStatus', 'Please enter a prompt', 'error');
        return;
    }
    
    await generateImage(
        prompt,
        document.getElementById('negativePrompt').value,
        parseInt(document.getElementById('steps').value),
        parseFloat(document.getElementById('guidance').value),
        parseInt(document.getElementById('width').value),
        parseInt(document.getElementById('height').value),
        1,
        'generateStatus',
        'generateResults'
    );
});

// ==================== GENERATE VIDEO ====================
document.getElementById('videoBtn').addEventListener('click', async () => {
    const prompt = document.getElementById('videoPrompt').value.trim();

    if (!prompt) {
        showStatus('videoStatus', 'Please enter a prompt', 'error');
        return;
    }

    showStatus('videoStatus', 'Generating video. The first run may take several minutes while the model loads...', 'loading');

    try {
        const response = await fetch(`${API_URL}/generate-video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                negative_prompt: document.getElementById('videoNegativePrompt').value,
                num_inference_steps: parseInt(document.getElementById('videoSteps').value),
                guidance_scale: parseFloat(document.getElementById('videoGuidance').value),
                width: parseInt(document.getElementById('videoWidth').value),
                height: parseInt(document.getElementById('videoHeight').value),
                num_frames: parseInt(document.getElementById('videoFrames').value),
                fps: parseInt(document.getElementById('videoFps').value)
            })
        });

        if (!response.ok) throw new Error(await getErrorMessage(response, 'Video generation failed'));

        const data = await response.json();
        showStatus('videoStatus', 'Video generated successfully!', 'success');
        displayVideoResult(data.video);
    } catch (error) {
        showStatus('videoStatus', `Error: ${error.message}`, 'error');
    }
});

// ==================== BATCH GENERATION ====================
document.getElementById('batchBtn').addEventListener('click', async () => {
    const prompt = document.getElementById('batchPrompt').value.trim();
    
    if (!prompt) {
        showStatus('batchStatus', 'Please enter a prompt', 'error');
        return;
    }
    
    await generateImage(
        prompt,
        document.getElementById('batchNegativePrompt').value,
        parseInt(document.getElementById('batchSteps').value),
        parseFloat(document.getElementById('batchGuidance').value),
        1024,
        1024,
        parseInt(document.getElementById('batchCount').value),
        'batchStatus',
        'batchResults'
    );
});

// ==================== IMAGE VARIATION ====================
document.getElementById('variationFile').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            const preview = document.getElementById('variationPreview');
            preview.innerHTML = `<img src="${event.target.result}" alt="Preview">`;
            document.getElementById('variationBtn').disabled = false;
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById('variationBtn').addEventListener('click', async () => {
    const file = document.getElementById('variationFile').files[0];
    if (!file) {
        showStatus('variationStatus', 'Please upload an image', 'error');
        return;
    }
    
    showStatus('variationStatus', 'Creating variation...', 'loading');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('request_data', JSON.stringify({
            prompt: document.getElementById('variationPrompt').value.trim() || 'a beautiful high quality image',
            negative_prompt: document.getElementById('variationNegativePrompt').value,
            strength: parseFloat(document.getElementById('variationStrength').value),
            num_inference_steps: parseInt(document.getElementById('variationSteps').value),
            guidance_scale: parseFloat(document.getElementById('variationGuidance').value),
            num_images: parseInt(document.getElementById('variationCount').value),
            nsfw_mode: currentNSFWMode,
            nsfw_model: currentNSFWModel
        }));
        
        const response = await fetch(`${API_URL}/variation`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error(await getErrorMessage(response, 'Variation generation failed'));
        
        const data = await response.json();
        
        const count = data.images ? data.images.length : 1;
        showStatus('variationStatus', `Created ${count} variation(s)!`, 'success');
        displayVariationResult(data);
    } catch (error) {
        showStatus('variationStatus', `Error: ${error.message}`, 'error');
    }
});

// ==================== GALLERY ====================
document.getElementById('refreshGalleryBtn').addEventListener('click', loadGallery);

document.getElementById('clearGalleryBtn').addEventListener('click', async () => {
    if (confirm('Are you sure you want to delete all images? This cannot be undone.')) {
        try {
            const response = await fetch(`${API_URL}/gallery`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to clear gallery');
            
            const data = await response.json();
            showStatus('galleryStatus', `Deleted ${data.deleted} images`, 'success');
            await loadGallery();
        } catch (error) {
            showStatus('galleryStatus', `Error: ${error.message}`, 'error');
        }
    }
});

// ==================== HELPER FUNCTIONS ====================

async function generateImage(prompt, negativePrompt, steps, guidance, width, height, numImages, statusId, resultsId) {
    showStatus(statusId, `Generating ${numImages} image(s)...`, 'loading');
    
    try {
        const endpoint = numImages > 1 ? '/generate-batch' : '/generate';
        
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                negative_prompt: negativePrompt,
                num_inference_steps: steps,
                guidance_scale: guidance,
                width,
                height,
                num_images: numImages,
                nsfw_mode: currentNSFWMode,
                nsfw_model: currentNSFWModel
            })
        });
        
        if (!response.ok) throw new Error(await getErrorMessage(response, 'Generation failed'));
        
        const data = await response.json();
        
        showStatus(statusId, `Successfully generated ${data.images.length} image(s)!`, 'success');
        displayResults(data.images, resultsId);
    } catch (error) {
        showStatus(statusId, `Error: ${error.message}`, 'error');
    }
}

async function enhancePrompt(promptId, negativePromptId, styleId, statusId) {
    const promptField = document.getElementById(promptId);
    const negativeField = document.getElementById(negativePromptId);
    const styleField = document.getElementById(styleId);
    const prompt = promptField.value.trim();

    if (!prompt) {
        showStatus(statusId, 'Enter a short prompt first.', 'error');
        return;
    }

    showStatus(statusId, 'Enhancing prompt...', 'loading');

    try {
        const response = await fetch(`${API_URL}/enhance-prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                style: styleField.value
            })
        });

        if (!response.ok) throw new Error(await getErrorMessage(response, 'Prompt enhancement failed'));

        const data = await response.json();
        promptField.value = data.prompt;
        negativeField.value = data.negative_prompt;
        const source = data.source === 'ai' ? 'AI prompt enhanced.' : 'Fallback prompt enhanced.';
        showStatus(statusId, `${source} Review it, then generate.`, 'success');
    } catch (error) {
        showStatus(statusId, `Error: ${error.message}`, 'error');
    }
}

function displayResults(images, resultsId) {
    const container = document.getElementById(resultsId);
    container.innerHTML = '';
    
    images.forEach(img => {
        const card = document.createElement('div');
        card.className = 'image-card';
        const image = document.createElement('img');
        image.src = `${API_URL}${img.url}`;
        image.alt = 'Generated image';
        image.loading = 'lazy';

        const info = document.createElement('div');
        info.className = 'image-info';

        const prompt = document.createElement('div');
        prompt.className = 'image-prompt';
        prompt.textContent = img.prompt || 'Generated image';

        const actions = document.createElement('div');
        actions.className = 'image-actions';
        actions.innerHTML = `
            <button onclick="downloadImage('${img.url}', '${img.filename}')" class="btn btn-secondary">Download</button>
            <button onclick="deleteImage('${img.filename}')" class="btn btn-danger">Delete</button>
        `;

        info.appendChild(prompt);
        info.appendChild(actions);
        card.appendChild(image);
        card.appendChild(info);
        container.appendChild(card);
    });
}

function displayVideoResult(video) {
    const container = document.getElementById('videoResults');
    container.innerHTML = '';

    const card = document.createElement('div');
    card.className = 'image-card media-card';

    const player = document.createElement('video');
    player.src = `${API_URL}${video.url}`;
    player.controls = true;
    player.loop = true;
    player.muted = true;
    player.playsInline = true;

    const info = document.createElement('div');
    info.className = 'image-info';

    const prompt = document.createElement('div');
    prompt.className = 'image-prompt';
    prompt.textContent = video.prompt || 'Generated video';

    const actions = document.createElement('div');
    actions.className = 'image-actions';
    actions.innerHTML = `
        <button onclick="downloadImage('${video.url}', '${video.filename}')" class="btn btn-secondary">Download</button>
        <button onclick="deleteImage('${video.filename}')" class="btn btn-danger">Delete</button>
    `;

    info.appendChild(prompt);
    info.appendChild(actions);
    card.appendChild(player);
    card.appendChild(info);
    container.appendChild(card);
}

function displayVariationResult(img) {
    if (Array.isArray(img.images)) {
        displayResults(img.images, 'variationResults');
        return;
    }

    const container = document.getElementById('variationResults');
    container.innerHTML = '';
    
    const card = document.createElement('div');
    card.className = 'image-card';
    card.innerHTML = `
        <img src="${API_URL}${img.url}" alt="Variation">
        <div class="image-info">
            <div class="image-prompt">Generated variation</div>
            <div class="image-actions">
                <button onclick="downloadImage('${img.url}', '${img.filename}')" class="btn btn-secondary">Download</button>
                <button onclick="deleteImage('${img.filename}')" class="btn btn-danger">Delete</button>
            </div>
        </div>
    `;
    container.appendChild(card);
}

async function loadGallery() {
    showStatus('galleryStatus', 'Loading gallery...', 'loading');
    
    try {
        const response = await fetch(`${API_URL}/gallery`);
        if (!response.ok) throw new Error(await getErrorMessage(response, 'Failed to load gallery'));
        
        const data = await response.json();
        
        const grid = document.getElementById('galleryGrid');
        grid.innerHTML = '';
        
        if (data.images.length === 0) {
            showStatus('galleryStatus', 'Gallery is empty. Generate some images.', 'success');
            return;
        }
        
        showStatus('galleryStatus', `Loaded ${data.total} image(s)`, 'success');
        
        data.images.forEach(img => {
            const item = document.createElement('div');
            item.className = 'gallery-item';
            if (img.type === 'video') {
                item.innerHTML = `
                    <video src="${API_URL}${img.url}" muted loop playsinline preload="metadata"></video>
                    <div class="gallery-item-overlay">
                        <button onclick="downloadImage('${img.url}', '${img.filename}')">Download</button>
                        <button onclick="deleteImage('${img.filename}')">Delete</button>
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <img src="${API_URL}${img.url}" alt="Gallery image" loading="lazy">
                    <div class="gallery-item-overlay">
                        <button onclick="downloadImage('${img.url}', '${img.filename}')">Download</button>
                        <button onclick="deleteImage('${img.filename}')">Delete</button>
                    </div>
                `;
            }
            grid.appendChild(item);
        });
    } catch (error) {
        showStatus('galleryStatus', `Error: ${error.message}`, 'error');
    }
}

async function deleteImage(filename) {
    if (!confirm('Delete this image?')) return;
    
    try {
        const response = await fetch(`${API_URL}/image/${filename}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error(await getErrorMessage(response, 'Delete failed'));
        
        // Reload gallery if on gallery tab
        const galleryTab = document.getElementById('gallery');
        if (galleryTab.classList.contains('active')) {
            await loadGallery();
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function downloadImage(url, filename) {
    const link = document.createElement('a');
    link.href = `${API_URL}${url}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.className = `status show ${type}`;
    element.textContent = message;
}

async function getErrorMessage(response, fallback) {
    try {
        const data = await response.json();
        return data.detail || fallback;
    } catch {
        return fallback;
    }
}

// Initialize on page load
window.addEventListener('load', initializeApp);
