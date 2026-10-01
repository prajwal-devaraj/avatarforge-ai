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

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const VALID_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

let originalObjectUrl = null;
let generatedObjectUrl = null;

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
        message.textContent = 'Please choose a JPG, PNG, or WEBP image.';
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

    generateButton.classList.add('loading');
    generateButton.disabled = true;
    generationOverlay.hidden = false;
    resultActions.hidden = true;
    message.textContent = '';
    setStatus('Processing', 'processing');
    previewTitle.textContent = 'Generating avatar';

    const body = new FormData();
    body.append('file', file);
    body.append('style', 'cartoon');

    try {
        const startedAt = performance.now();
        const response = await fetch('/generate', { method: 'POST', body });
        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload.error || 'Generation failed. Please try again.');
        }

        const blob = await response.blob();
        const elapsed = Math.max(0.1, (performance.now() - startedAt) / 1000).toFixed(1);

        if (generatedObjectUrl) URL.revokeObjectURL(generatedObjectUrl);
        generatedObjectUrl = URL.createObjectURL(blob);
        generatedPreview.src = generatedObjectUrl;
        downloadButton.href = generatedObjectUrl;
        document.getElementById('generation-meta').textContent = `Signature Cartoon · High quality · ${elapsed}s`;
        resultActions.hidden = false;
        setStatus('Complete', 'complete');
        previewTitle.textContent = 'Avatar complete';
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
