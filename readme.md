# AvatarForge AI

**Your face. Your style. Your digital identity.**

AvatarForge AI is an evolving digital identity platform for transforming personal photos into expressive avatars. The current release introduces a company-style product experience around a fast computer-vision cartoon renderer, with a roadmap toward professional portraits, anime, gaming identities, and generative AI styles.

## Current Release — Step 2

- Premium, responsive product landing page
- AvatarForge AI branding and visual system
- Drag-and-drop image upload
- JPG, PNG, and WEBP validation
- 10 MB upload limit
- Improved OpenCV cartoon rendering
- Correct RGB/BGR image handling
- In-page before/after preview
- Direct result download
- Mobile navigation and responsive layout
- Accessible controls and reduced-motion support

## Technology

- **Backend:** Python, Flask
- **Image processing:** OpenCV, NumPy, Pillow
- **Frontend:** HTML, CSS, vanilla JavaScript

> The current image engine is computer vision, not a generative AI model. Generative AI is part of the product roadmap and will be introduced as a later platform step.

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

Open `http://127.0.0.1:5000`.

## Project structure

```text
avatarforge-ai/
├── app.py
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html
└── readme.md
```

## Product roadmap

1. Brand foundation — complete
2. Company-level landing page — complete
3. Dedicated avatar generation workspace
4. Multiple image styles and controls
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

## Avatar Studio Workspace

The `/studio` route provides a dedicated creation workspace with drag-and-drop upload, source preview, style selection, generation state, side-by-side original/result comparison, regeneration, and direct download actions.

Current production engine: **Signature Cartoon**, powered by OpenCV image processing. Additional generative styles remain intentionally marked as coming soon until real model-backed implementations are added.
