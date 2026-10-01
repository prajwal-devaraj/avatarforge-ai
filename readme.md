# AvatarForge AI

**Your face. Your style. Your digital identity.**

AvatarForge AI is an evolving digital identity platform for transforming personal photos into expressive avatars. The current release combines a company-style product experience with a multi-style computer-vision rendering engine and adjustable style intensity.

## Current Release — Step 6

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
5. Modular backend architecture — complete
6. Versioned API foundation — complete
7. PostgreSQL and authentication
8. Generative AI avatar models
9. Generation history and cloud storage
10. Background workers, developer API, observability, billing, and production deployment

## Product direction

AvatarForge AI is being designed as more than a filter utility. The long-term platform will support professional portraits, creator identities, gaming avatars, artistic transformations, developer integrations, and privacy-conscious AI generation workflows.

---

Built by **Prajwal Devaraj**.

## Backend architecture

Step 5 reorganizes the application around clear responsibilities while preserving the existing Flask routes and UI:

- `routes/` owns HTTP/page routing only.
- `services/` owns image decoding, style engines, and generation orchestration.
- `utils/` contains small reusable validation and image helpers.
- `config.py` centralizes environment-aware Flask configuration.
- `tests/` adds unit and route-level coverage for core behavior.
- `app.py` now uses an application factory, making testing and future deployment easier.

Run the test suite with:

```bash
pytest -q
```


## API v1

Step 6 introduces a versioned JSON API while preserving the legacy `/generate` route during migration.

- `GET /api/v1/health` — service health and API version
- `GET /api/v1/styles` — registered visual styles
- `POST /api/v1/generate` — multipart avatar generation with a standardized JSON response
- Every v1 response uses `success`, `data`, `error`, and `meta` fields.
- Every request receives an `X-Request-ID`; callers may also supply one for trace correlation.
- Generation responses include processing time metadata and a base64-encoded JPEG payload.

Example success envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "..."
  }
}
```

The browser Studio now consumes `/api/v1/generate`. The original `/generate` endpoint remains temporarily available for backward compatibility and is marked deprecated in its response headers.
