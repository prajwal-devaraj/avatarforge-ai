# AvatarForge AI

**Your face. Your style. Your digital identity.**

AvatarForge AI is an evolving digital identity and avatar platform. The current release combines a polished Flask product experience, a versioned API, a modular computer-vision rendering engine, secure account sessions, and private saved-generation history.

## Step 7 capabilities

- Six working image styles with configurable intensity
- Dedicated Avatar Studio and before/after preview
- Versioned `/api/v1` API with standardized response contracts
- Email/password account registration and sign-in
- Werkzeug password hashing
- CSRF protection for account form actions
- Private generated-image history with ownership checks
- Request-scoped source uploads; source images are not persisted by the history feature
- SQLAlchemy data models
- SQLite for zero-configuration local development
- PostgreSQL-ready `DATABASE_URL` configuration
- Alembic migration baseline
- Private generated outputs stored outside the public `static/` directory
- Automated test coverage for API, auth, persistence, validation, and image processing

## Architecture

```text
Browser
  |
  +--> Flask page/auth routes
  |
  +--> /api/v1/generate
          |
          +--> validation
          +--> generation_service
          +--> image_service (OpenCV)
          +--> JPEG response
          |
          +--> signed-in user?
                  |
                  +--> private generated output
                  +--> SQLAlchemy Generation record

Database
  Local: SQLite
  Production target: PostgreSQL
```

## Local setup

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the tests:

```powershell
python -m pytest -q
```

Start the application:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
http://127.0.0.1:5000/studio
```

## Accounts and generation history

Account routes:

```text
/auth/register
/auth/login
/generations
```

Guests can continue generating avatars. When a user is signed in, successful generations are automatically saved to that user's private history. The source upload itself is not written to the history store.

Generated images are written under `instance/generated/<user-id>/` and served only through an ownership-checked route.

## Database configuration

Without configuration, local development uses:

```text
instance/avatarforge.db
```

For PostgreSQL, set `DATABASE_URL`, for example:

```text
DATABASE_URL=postgresql://avatarforge:password@localhost:5432/avatarforge
```

The application normalizes PostgreSQL URLs for the Psycopg 3 SQLAlchemy driver.

Before production deployment, set a strong secret:

```text
AVATARFORGE_SECRET_KEY=<long-random-secret>
AVATARFORGE_ENV=production
```

See `.env.example` for the supported variables.

## Database migrations

Step 7 includes an Alembic baseline for `users` and `generations`.

For a fresh production database:

```powershell
alembic upgrade head
```

Development mode also creates missing tables automatically for a frictionless local start. Production deployment should use migrations as the source of truth.

## API v1

### Health

```http
GET /api/v1/health
```

### Styles

```http
GET /api/v1/styles
```

### Generate

```http
POST /api/v1/generate
Content-Type: multipart/form-data
```

Fields:

```text
file=<JPG/PNG/WEBP>
style=cartoon|sketch|comic|portrait|grayscale|edgepop
intensity=10..100
```

When authenticated, the response includes a saved generation ID and private history links. Guests receive the same generated image without persistence.

## Privacy direction

AvatarForge is being built around explicit ownership and controlled retention. In this release:

- source uploads are processed in-memory for the request and are not persisted to account history;
- generated outputs are persisted only for signed-in users;
- saved output routes verify that the current account owns the requested generation;
- local database files, private generated assets, secrets, and environment files are ignored by Git.

## Current technology

- Python
- Flask
- SQLAlchemy 2
- Alembic
- PostgreSQL-ready Psycopg 3 configuration
- SQLite local development
- OpenCV
- Pillow
- NumPy
- HTML / CSS / JavaScript
- Pytest

## Roadmap

The next milestones are cloud object storage, asynchronous generation workers, real generative-AI inference, observability, and production deployment infrastructure.


## Generative AI mode
Step 8 adds a provider-neutral AI generation layer. Set `AVATARFORGE_AI_ENDPOINT` and optionally `AVATARFORGE_AI_API_KEY` to connect a remote image-to-image service that accepts multipart fields `image`, `prompt`, `style`, and `intensity`, and returns JSON containing `image_base64`. Classic OpenCV mode remains available as a local fallback.


## Step 9: Optional fal.ai production provider

AvatarForge now includes a server-side `fal` provider for real image-to-image generation with `fal-ai/flux-pro/kontext`. The integration is optional: the project continues to run in Classic mode or with the built-in mock AI provider without any external account.

For local development without a key:

```powershell
$env:AVATARFORGE_AI_PROVIDER="mock"
python app.py
```

When you later create a fal.ai key, keep it outside source control and switch providers:

```powershell
$env:AVATARFORGE_AI_PROVIDER="fal"
$env:FAL_KEY="your-key-here"
python app.py
```

Never place a real API key in `.env.example`, Git commits, frontend JavaScript, screenshots, or issue reports. The browser continues to call AvatarForge's own backend; the provider credential remains server-side.
