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
- Automated tests for API, auth, persistence, AI-provider abstraction, image processing, job lifecycle, storage, and observability
- Local or S3-compatible private object storage with lifecycle cleanup
- Automatic generation retries with configurable attempt limits
- Prometheus metrics, readiness checks, request correlation IDs, and optional JSON logs

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

Rate limiting, abuse protection, CI/CD deployment pipelines, admin analytics, billing/usage controls, and production cloud deployment.

## Production runtime with Docker

Step 11 adds a containerized production runtime built around Gunicorn, PostgreSQL, Redis, RQ workers, Alembic migrations, health checks, and shared private generation storage.

### Local Docker stack

1. Copy `.env.docker.example` to `.env`.
2. Replace `AVATARFORGE_SECRET_KEY` and `POSTGRES_PASSWORD` with strong local values.
3. Keep `AVATARFORGE_AI_PROVIDER=mock` until a real AI provider key is available.
4. Start the stack:

```bash
docker compose up --build
```

The web application is available at `http://localhost:8000` by default. Docker Compose starts:

- `web` — Flask served by Gunicorn
- `worker` — RQ background generation worker
- `db` — PostgreSQL
- `redis` — Redis queue backend

The web container applies Alembic migrations before Gunicorn starts. Generated files and job outputs are stored in a shared private Docker volume so the web and worker containers see the same data.

### Production environment notes

Set `AVATARFORGE_ENV=production`, provide a long random `AVATARFORGE_SECRET_KEY`, use a managed PostgreSQL database and Redis service, and set `AVATARFORGE_SESSION_COOKIE_SECURE=1` behind HTTPS. Set `AVATARFORGE_TRUST_PROXY_HEADERS=1` only when the application is actually behind a trusted reverse proxy or load balancer that sets forwarding headers.

Never commit `.env`, `FAL_KEY`, database passwords, or production secrets.

### Direct Gunicorn runtime

Outside Docker, production can be started with:

```bash
alembic upgrade head
gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 180 wsgi:app
```

For RQ-backed generation jobs, run a separate worker process connected to the same Redis instance and shared generation storage.

## Step 12: storage lifecycle and observability

Step 12 introduces a storage abstraction, retry policy, maintenance utilities, readiness checks, structured logging, and Prometheus-compatible metrics.

### Storage backends

Local filesystem storage remains the zero-setup default:

```powershell
$env:AVATARFORGE_STORAGE_BACKEND="local"
python app.py
```

For S3 or an S3-compatible object store:

```text
AVATARFORGE_STORAGE_BACKEND=s3
AVATARFORGE_S3_BUCKET=your-private-bucket
AVATARFORGE_S3_PREFIX=avatarforge
AVATARFORGE_S3_REGION=us-east-1
AVATARFORGE_S3_ENDPOINT_URL=
AVATARFORGE_S3_ACCESS_KEY_ID=...
AVATARFORGE_S3_SECRET_ACCESS_KEY=...
```

Generated objects are private and are read through authenticated/token-protected AvatarForge routes rather than exposed as public bucket URLs. Server-side encryption defaults to `AES256` for S3 uploads.

### Retry policy

Generation jobs track `attempt_count` and `max_attempts`. The default policy allows two total attempts:

```text
AVATARFORGE_JOB_MAX_ATTEMPTS=2
```

Temporary source input is retained between retry attempts and removed after the job reaches a terminal state.

### Lifecycle cleanup

Terminal job records and job-only result artifacts can be cleaned after a configurable retention window. Saved account history is not deleted by this maintenance command.

```powershell
python maintenance.py cleanup-jobs
python maintenance.py cleanup-jobs --older-than-hours 48
```

Default retention:

```text
AVATARFORGE_JOB_RETENTION_HOURS=24
```

### Health, readiness, and metrics

```text
GET /api/v1/health
GET /api/v1/ready
GET /api/v1/metrics
```

`/health` confirms the web process is alive. `/ready` checks database and storage readiness. `/metrics` exposes Prometheus-format request, latency, generation, retry, and active-job metrics.

### Structured logs

Enable JSON logs in production:

```text
AVATARFORGE_JSON_LOGS=1
AVATARFORGE_LOG_LEVEL=INFO
```

Request IDs are included in structured request-context logs and returned through `X-Request-ID`.

### Development database compatibility

Fresh development databases are created with the Step 12 retry fields. Existing local SQLite databases created by earlier AvatarForge steps are automatically upgraded with the two additive retry columns during development startup. Production deployments should continue to use Alembic:

```powershell
python -m alembic upgrade head
```

## Developer API

Step 13 adds developer API keys, monthly generation quotas, and per-minute rate limiting.
API keys are shown only once and are stored as SHA-256 hashes. Send a key with
`Authorization: Bearer af_live_...` when calling generation endpoints. Signed-in
users can create, list, revoke, and inspect usage for their keys through the
`/api/v1/developer/*` endpoints.

Local development uses an in-memory rate limiter. Distributed deployments should
set `AVATARFORGE_RATE_LIMIT_BACKEND=redis` and provide `REDIS_URL`.

## Vercel deployment target

AvatarForge is being kept compatible with a final Vercel deployment. The Flask
web application can run on Vercel's Python runtime, while durable production data
must live outside the function filesystem. The final deployment step will use a
managed Postgres database, Redis-compatible rate limiting/queue infrastructure,
and private object storage rather than local SQLite or local generated-image
folders.
