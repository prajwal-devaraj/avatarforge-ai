# AvatarForge AI

**Your face. Your style. Your digital identity.**

AvatarForge AI is an evolving digital identity platform for transforming personal photos into expressive avatars. The current release combines a company-style product experience with a multi-style computer-vision rendering engine and adjustable style intensity.

## Current Release — Step 4

- Premium, responsive product landing page
- Dedicated `/studio` avatar-generation workspace
- Drag-and-drop image upload with source preview
- JPG, PNG, and WEBP validation with a 10 MB limit
- Six working visual styles:
  - Signature Cartoon
  - Pencil Sketch
  - Comic Ink
  - Soft Portrait
  - Grayscale Art
  - Edge Pop
- Adjustable 10–100% style intensity
- Side-by-side original/result comparison
- Dynamic style labels and generation metadata
- Regenerate and direct-download actions
- Improved image processing with OpenCV, NumPy, and Pillow
- Correct RGB/BGR color handling
- Responsive controls for desktop and mobile

## Technology

- **Backend:** Python, Flask
- **Image processing:** OpenCV, NumPy, Pillow
- **Frontend:** HTML, CSS, vanilla JavaScript

> Step 4 uses deterministic computer-vision image transformations rather than a generative AI model. Model-backed generative styles are intentionally reserved for the later AI phase so the product remains technically accurate.

## Run locally

```bash
git clone <your-repository-url>
cd avatarforge-ai
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` for the landing page and `http://127.0.0.1:5000/studio` for Avatar Studio.

## Project structure

```text
avatarforge-ai/
├── app.py
├── requirements.txt
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── studio.css
│   └── js/
│       ├── app.js
│       └── studio.js
├── templates/
│   ├── index.html
│   └── studio.html
└── readme.md
```

## Product roadmap

1. Brand foundation — complete
2. Company-level landing page — complete
3. Dedicated avatar generation workspace — complete
4. Multiple image styles and controls — complete
5. FastAPI service architecture
6. PostgreSQL and authentication
7. Generative AI avatar models
8. Generation history and cloud storage
9. Background workers and scalable inference
10. Developer API, observability, billing, and production deployment

## Product direction

AvatarForge AI is being designed as more than a filter utility. The long-term platform will support professional portraits, creator identities, gaming avatars, artistic transformations, developer integrations, and privacy-conscious AI generation workflows.

---

Built by **Prajwal Devaraj**.
