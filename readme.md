# AvatarForge AI

**Your face. Your style. Your digital identity.**

AvatarForge AI is an evolving avatar and digital-identity platform combining a polished Flask product experience, computer-vision styles, optional generative-AI providers, secure accounts, private history, and asynchronous generation jobs.

## Current capabilities

- Six local image styles with configurable intensity
- Classic OpenCV mode and provider-neutral AI mode
- Optional fal.ai image-to-image provider plus mock and generic remote providers
- Versioned `/api/v1` API with request IDs and standardized responses
- Email/password registration, login, logout, CSRF protection, and private history
- SQLAlchemy models, SQLite local development, PostgreSQL-ready configuration, and Alembic migrations
- Asynchronous generation job model with queued / processing / completed / failed states
- Built-in local background-thread worker for zero-setup development
- Redis/RQ-ready production queue backend
- Job progress polling from the Avatar Studio frontend
- Temporary source-image staging for background jobs; source files are deleted after processing
- Access-token protection for anonymous job status/results and account ownership for signed-in users
- Automated tests for API, auth, persistence, AI-provider abstraction, image processing, and job lifecycle

## Step 10 architecture

```text
Browser
  |
  +--> POST /api/v1/jobs
          |
          +--> validate request
          +--> persist GenerationJob
          +--> temporarily stage source image
          +--> queue backend
                   |
                   +--> thread (local default)
                   +--> inline (tests)
                   +--> Redis/RQ (production-ready)
                            |
                            +--> worker.py
                                      |
                                      +--> classic OpenCV OR AI provider
                                      +--> save job result
                                      +--> optionally save account history
                                      +--> delete temporary source image

Browser
  |
  +--> GET /api/v1/jobs/<id>        # poll status/progress
  +--> GET /api/v1/jobs/<id>/image  # fetch completed result
```

The previous synchronous `POST /api/v1/generate` endpoint remains available for compatibility, while the Studio now uses the asynchronous job flow.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python app.py
```

Open:

```text
http://127.0.0.1:5000
http://127.0.0.1:5000/studio
```

The local queue backend defaults to `thread`, so Redis is not required for normal development.

## Job backends

### Local background worker

Default:

```powershell
$env:AVATARFORGE_JOB_BACKEND="thread"
python app.py
```

This executes jobs in a small in-process thread pool and is designed for local development.

### Deterministic inline mode

Useful for tests and debugging:

```powershell
$env:AVATARFORGE_JOB_BACKEND="inline"
python app.py
```

### Redis/RQ mode

For a multi-process deployment:

```powershell
$env:AVATARFORGE_JOB_BACKEND="rq"
$env:REDIS_URL="redis://localhost:6379/0"
python app.py
```

Start an RQ worker separately from the project directory:

```powershell
rq worker avatarforge --url redis://localhost:6379/0
```

Queued RQ jobs call `worker.run_generation_job` and create their own Flask application context.

## Async API

### Create job

```http
POST /api/v1/jobs
Content-Type: multipart/form-data
```

Fields:

```text
file=<JPG/PNG/WEBP>
style=cartoon|sketch|comic|portrait|grayscale|edgepop
intensity=10..100
engine=classic|ai
prompt=<optional AI prompt>
```

The response is `202 Accepted` and includes a job ID plus an unguessable access token used by anonymous clients.

### Poll status

```http
GET /api/v1/jobs/<job-id>
X-Job-Token: <token>
```

Status values:

```text
queued
processing
completed
failed
```

### Fetch result

```http
GET /api/v1/jobs/<job-id>/image
X-Job-Token: <token>
```

Signed-in users can also access their own jobs through their authenticated session.

## AI provider modes

Without any external key:

```powershell
$env:AVATARFORGE_AI_PROVIDER="mock"
python app.py
```

For the optional fal.ai provider later:

```powershell
$env:AVATARFORGE_AI_PROVIDER="fal"
$env:FAL_KEY="your-real-key"
python app.py
```

Never commit API keys. `.env` and `instance/` are ignored by Git.

## Database and migrations

Local development defaults to:

```text
instance/avatarforge.db
```

Production can use PostgreSQL through `DATABASE_URL`.

Run migrations with:

```powershell
python -m alembic upgrade head
```

Step 10 adds the `generation_jobs` migration after the existing user/generation migration.

## Privacy and storage behavior

- Background jobs temporarily stage source uploads under `instance/jobs/<job-id>/`.
- The worker deletes the source image after success or failure.
- Completed job outputs are kept under the private `instance/` tree, not under public static assets.
- Anonymous jobs require a generated job access token to read status/results.
- Signed-in generations can additionally be saved to the user's private history.
- Secrets, local database files, staged inputs, and generated files are excluded from source control.

## Technology

Python, Flask, SQLAlchemy 2, Alembic, PostgreSQL/Psycopg 3, SQLite, OpenCV, Pillow, NumPy, Redis, RQ, fal-client, HTML/CSS/JavaScript, and Pytest.

## Next milestones

Cloud object storage, job expiry/cleanup policies, retries and dead-letter handling, observability, rate limiting, production deployment, and billing/usage controls.
