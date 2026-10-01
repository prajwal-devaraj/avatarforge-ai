const form = document.getElementById('avatar-form');
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const selectedFile = document.getElementById('selected-file');
const generateButton = document.getElementById('generate-button');
const formMessage = document.getElementById('form-message');
const generatorCard = document.getElementById('generator-card');
const resultPanel = document.getElementById('result-panel');
const originalPreview = document.getElementById('original-preview');
const generatedPreview = document.getElementById('generated-preview');
const downloadButton = document.getElementById('download-button');
const resetButton = document.getElementById('reset-button');
const menuToggle = document.querySelector('.menu-toggle');
const siteNav = document.querySelector('.site-nav');

let originalObjectUrl = null;
let generatedObjectUrl = null;

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const VALID_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

function setFile(file) {
    formMessage.textContent = '';
    if (!file) {
        selectedFile.textContent = '';
        generateButton.disabled = true;
        return;
    }
    if (!VALID_TYPES.includes(file.type)) {
        formMessage.textContent = 'Please choose a JPG, PNG, or WEBP image.';
        fileInput.value = '';
        generateButton.disabled = true;
        return;
    }
    if (file.size > MAX_FILE_SIZE) {
        formMessage.textContent = 'That image is larger than 10 MB.';
        fileInput.value = '';
        generateButton.disabled = true;
        return;
    }
    selectedFile.textContent = file.name;
    generateButton.disabled = false;
}

fileInput.addEventListener('change', () => setFile(fileInput.files[0]));

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
    setFile(file);
});

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;

    generateButton.classList.add('loading');
    generateButton.disabled = true;
    formMessage.textContent = 'Forging your avatar…';

    const data = new FormData();
    data.append('file', file);

    try {
        const response = await fetch('/generate', { method: 'POST', body: data });
        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload.error || 'Generation failed. Please try again.');
        }

        const blob = await response.blob();
        if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
        if (generatedObjectUrl) URL.revokeObjectURL(generatedObjectUrl);

        originalObjectUrl = URL.createObjectURL(file);
        generatedObjectUrl = URL.createObjectURL(blob);
        originalPreview.src = originalObjectUrl;
        generatedPreview.src = generatedObjectUrl;
        downloadButton.href = generatedObjectUrl;

        generatorCard.hidden = true;
        resultPanel.hidden = false;
        formMessage.textContent = '';
        resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (error) {
        formMessage.textContent = error.message;
    } finally {
        generateButton.classList.remove('loading');
        generateButton.disabled = !fileInput.files[0];
    }
});

resetButton.addEventListener('click', () => {
    resultPanel.hidden = true;
    generatorCard.hidden = false;
    fileInput.value = '';
    selectedFile.textContent = '';
    generateButton.disabled = true;
    formMessage.textContent = '';
});

menuToggle.addEventListener('click', () => {
    const isOpen = siteNav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
});

document.querySelectorAll('.site-nav a').forEach((link) => {
    link.addEventListener('click', () => {
        siteNav.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
    });
});

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
document.getElementById('year').textContent = new Date().getFullYear();
