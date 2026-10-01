const form = document.getElementById('studio-form');
const fileInput = document.getElementById('studio-file-input');
const dropZone = document.getElementById('studio-dropzone');
const selectedFileRow = document.getElementById('studio-selected-file');
const fileName = document.getElementById('studio-file-name');
const removeFileButton = document.getElementById('remove-file');
const generateButton = document.getElementById('studio-generate-button');
const message = document.getElementById('studio-message');
const emptyState = document.getElementById('empty-state');
const comparisonView = document.getElementById('comparison-view');
const originalPreview = document.getElementById('studio-original-preview');
const generatedPreview = document.getElementById('studio-generated-preview');
const generationOverlay = document.getElementById('generation-overlay');
const resultActions = document.getElementById('result-actions');
const downloadButton = document.getElementById('studio-download-button');
const regenerateButton = document.getElementById('regenerate-button');
const canvasStatus = document.getElementById('canvas-status');
const previewTitle = document.getElementById('preview-title');
const intensityInput = document.getElementById('style-intensity');
const intensityValue = document.getElementById('intensity-value');
const resultStyleBadge = document.getElementById('result-style-badge');
const generationMeta = document.getElementById('generation-meta');
const styleOptions = [...document.querySelectorAll('.style-option')];

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const VALID_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

let originalObjectUrl = null;
let generatedObjectUrl = null;

function selectedStyle() {
    const input = document.querySelector('input[name="style"]:checked');
    const option = input?.closest('.style-option');
    return {
        value: input?.value || 'cartoon',
        label: option?.dataset.styleLabel || 'Signature Cartoon',
    };
}

function setStatus(label, state = '') {
    canvasStatus.className = `canvas-status ${state}`.trim();
    canvasStatus.innerHTML = `<span></span> ${label}`;
}

function clearGeneratedResult() {
    if (generatedObjectUrl) {
        URL.revokeObjectURL(generatedObjectUrl);
        generatedObjectUrl = null;
    }
    generatedPreview.removeAttribute('src');
    resultActions.hidden = true;
}

function previewSelectedFile(file) {
    if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
    originalObjectUrl = URL.createObjectURL(file);
    originalPreview.src = originalObjectUrl;
    emptyState.hidden = true;
    comparisonView.hidden = false;
    previewTitle.textContent = 'Generation workspace';
    clearGeneratedResult();
    setStatus('Ready');
}

function resetFile() {
    fileInput.value = '';
    selectedFileRow.hidden = true;
    fileName.textContent = '';
    message.textContent = '';
    generateButton.disabled = true;
    clearGeneratedResult();
    if (originalObjectUrl) {
        URL.revokeObjectURL(originalObjectUrl);
        originalObjectUrl = null;
    }
    originalPreview.removeAttribute('src');
    comparisonView.hidden = true;
    emptyState.hidden = false;
    previewTitle.textContent = 'Workspace';
    setStatus('Ready');
}

function acceptFile(file) {
    message.textContent = '';
    if (!file) return false;

    if (!VALID_TYPES.includes(file.type)) {
        resetFile();
        message.textContent = 'Please choose a JPG, PNG, or WEBP image.';
        return false;
    }

    if (file.size > MAX_FILE_SIZE) {
        resetFile();
        message.textContent = 'Image is larger than the 10 MB upload limit.';
        return false;
    }

    selectedFileRow.hidden = false;
    fileName.textContent = file.name;
    generateButton.disabled = false;
    previewSelectedFile(file);
    return true;
}

fileInput.addEventListener('change', () => acceptFile(fileInput.files[0]));
removeFileButton.addEventListener('click', resetFile);

styleOptions.forEach((option) => {
    const radio = option.querySelector('input[type="radio"]');
    radio.addEventListener('change', () => {
        styleOptions.forEach((item) => item.classList.toggle('active', item === option));
        const style = selectedStyle();
        resultStyleBadge.textContent = style.label;
        clearGeneratedResult();
        if (fileInput.files[0]) {
            previewTitle.textContent = `${style.label} selected`;
            setStatus('Ready');
        }
    });
});

intensityInput.addEventListener('input', () => {
    intensityValue.textContent = `${intensityInput.value}%`;
    clearGeneratedResult();
    if (fileInput.files[0]) setStatus('Ready');
});

dropZone.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        fileInput.click();
    }
});

['dragenter', 'dragover'].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add('dragover');
    });
});

['dragleave', 'drop'].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove('dragover');
    });
});

dropZone.addEventListener('drop', (event) => {
    const file = event.dataTransfer.files[0];
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    acceptFile(file);
});

async function generateAvatar() {
    const file = fileInput.files[0];
    if (!file) return;

    const style = selectedStyle();
    const intensity = intensityInput.value;

    generateButton.classList.add('loading');
    generateButton.disabled = true;
    generationOverlay.hidden = false;
    resultActions.hidden = true;
    message.textContent = '';
    setStatus('Processing', 'processing');
    previewTitle.textContent = `Generating ${style.label}`;
    resultStyleBadge.textContent = style.label;

    const body = new FormData();
    body.append('file', file);
    body.append('style', style.value);
    body.append('intensity', intensity);

    try {
        const startedAt = performance.now();
        const response = await fetch('/api/v1/generate', { method: 'POST', body });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok || !payload.success) {
            throw new Error(payload?.error?.message || 'Generation failed. Please try again.');
        }

        const elapsed = Math.max(0.1, (performance.now() - startedAt) / 1000).toFixed(1);
        const image = payload.data.image;
        const binary = atob(image.base64);
        const bytes = new Uint8Array(binary.length);
        for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
        const blob = new Blob([bytes], { type: image.mime_type });

        if (generatedObjectUrl) URL.revokeObjectURL(generatedObjectUrl);
        generatedObjectUrl = URL.createObjectURL(blob);
        generatedPreview.src = generatedObjectUrl;
        downloadButton.href = generatedObjectUrl;
        downloadButton.download = image.download_name;
        const serverMs = payload.meta?.processing_ms;
        const serverLabel = Number.isFinite(serverMs) ? ` · ${serverMs}ms server` : '';
        const savedLabel = payload.data.generation?.saved ? ' · Saved to history' : '';
        generationMeta.textContent = `${style.label} · ${intensity}% intensity · ${elapsed}s${serverLabel}${savedLabel}`;
        resultActions.hidden = false;
        setStatus('Complete', 'complete');
        previewTitle.textContent = `${style.label} complete`;
    } catch (error) {
        message.textContent = error.message;
        setStatus('Error');
        previewTitle.textContent = 'Generation workspace';
    } finally {
        generationOverlay.hidden = true;
        generateButton.classList.remove('loading');
        generateButton.disabled = !fileInput.files[0];
    }
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    await generateAvatar();
});

regenerateButton.addEventListener('click', generateAvatar);

window.addEventListener('beforeunload', () => {
    if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
    if (generatedObjectUrl) URL.revokeObjectURL(generatedObjectUrl);
});
