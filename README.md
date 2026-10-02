# AvatarForge AI

**Your face. Your style. Your digital identity.**

AvatarForge AI is a production-oriented AI avatar and digital identity platform built as a complete SaaS product, not just an image filter demo.

It combines:

- computer vision avatar styles
- optional generative AI providers
- secure authentication
- private generation history
- asynchronous generation jobs
- developer APIs
- API keys and usage quotas
- rate limiting
- billing infrastructure
- email verification
- password recovery
- observability
- PostgreSQL persistence
- object storage abstraction
- Vercel deployment support

The project evolved from a local Flask + OpenCV prototype into a cloud-ready platform architecture designed for real users, developers, and future AI product expansion.

---

# Live Demo

**Production:**  
https://avatarforge-ai.vercel.app

**GitHub:**  
https://github.com/prajwal-devaraj/avatarforge-ai

---

# What AvatarForge AI Does

AvatarForge AI lets users upload an image and generate stylized avatar outputs through either:

## Classic Mode

Local image processing powered by OpenCV.

Available styles include:

- Signature Cartoon
- Pencil Sketch
- Comic Ink
- Soft Portrait
- Grayscale Art
- Edge Pop

Users can also control transformation intensity.

## AI Mode

Provider-neutral generative AI architecture supporting:

- mock AI provider for local development
- fal.ai image-to-image integration
- generic remote AI provider support

The AI layer is intentionally abstracted so additional providers can be introduced without rewriting the application.

---

# Core Product Experience

The platform includes:

- premium landing page
- dedicated Avatar Studio
- image upload workflow
- style selection
- intensity controls
- Classic / AI mode switching
- optional AI prompt
- asynchronous generation
- progress polling
- secure result delivery
- download support
- user accounts
- saved private generation history
- account settings
- billing and usage dashboard
- developer API access

---

# Key Features

## Avatar Generation

- six built-in image styles
- configurable transformation intensity
- OpenCV-based local generation
- generative AI provider abstraction
- fal.ai integration
- mock provider for development and testing
- generic remote-provider support

---

## Asynchronous Job System

Avatar generation can run through a job-based architecture.

Supported states:

```text
queued
processing
completed
failed
```

The Studio creates generation jobs and polls their status until completion.

Supported execution backends:

```text
thread
inline
rq
```

### Thread Backend

Default local-development worker.

```powershell
$env:AVATARFORGE_JOB_BACKEND="thread"
python app.py
```

### Inline Backend

Useful for:

- tests
- debugging
- serverless execution
- Vercel demo deployments

```powershell
$env:AVATARFORGE_JOB_BACKEND="inline"
python app.py
```

### Redis / RQ Backend

Designed for distributed production processing.

```powershell
$env:AVATARFORGE_JOB_BACKEND="rq"
$env:REDIS_URL="redis://localhost:6379/0"

python app.py
```

Worker:

```powershell
rq worker avatarforge --url redis://localhost:6379/0
```

---

# Generation Architecture

```text
Browser / Avatar Studio
        |
        v
POST /api/v1/jobs
        |
        v
Request Validation
        |
        v
GenerationJob persisted
        |
        v
Input stored
        |
        v
Queue Backend
   /       |       \
thread   inline    Redis/RQ
        |
        v
Generation Worker
   /            \
Classic CV     AI Provider
        |
        v
Result Storage
        |
        +--> Job Result
        |
        +--> Optional User History
        |
        v
Frontend Polling
        |
        +--> GET /api/v1/jobs/<id>
        |
        +--> GET /api/v1/jobs/<id>/image
```

---

# API

AvatarForge exposes a versioned API under:

```text
/api/v1
```

## Health

```http
GET /api/v1/health
```

Confirms that the web application is alive.

## Readiness

```http
GET /api/v1/ready
```

Checks service readiness including database and storage dependencies.

## Metrics

```http
GET /api/v1/metrics
```

Returns Prometheus-compatible application metrics.

## Styles

```http
GET /api/v1/styles
```

Returns supported generation styles.

## Synchronous Generation

```http
POST /api/v1/generate
```

Maintained for compatibility.

## Create Async Job

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
prompt=<optional>
```

The endpoint returns:

```text
202 Accepted
```

with:

- job ID
- anonymous job access token
- job status

## Poll Job

```http
GET /api/v1/jobs/<job-id>
X-Job-Token: <token>
```

## Get Job Result

```http
GET /api/v1/jobs/<job-id>/image
X-Job-Token: <token>
```

Signed-in users can access jobs associated with their accounts without anonymous job tokens.

---

# Authentication

AvatarForge includes secure user authentication with:

- registration
- login
- logout
- password hashing
- CSRF protection
- session management
- authenticated private history

Routes include:

```text
/auth/register
/auth/login
/auth/logout
```

---

# Email Verification

AvatarForge supports signed and time-limited email verification links.

Routes include:

```text
/auth/verify-email/<token>
/auth/resend-verification
```

Production can require verified accounts:

```text
AVATARFORGE_EMAIL_VERIFICATION_REQUIRED=1
```

---

# Password Recovery

The platform includes:

- forgot-password flow
- signed reset links
- expiring reset tokens
- password update
- automatic reset-token invalidation after password changes

Routes:

```text
/auth/forgot-password
/auth/reset-password/<token>
```

---

# Email Backends

Supported transactional email backends:

```text
console
smtp
resend
```

## Local Development

```text
AVATARFORGE_EMAIL_BACKEND=console
AVATARFORGE_EMAIL_VERIFICATION_REQUIRED=0
```

## Vercel / Production

Recommended:

```text
AVATARFORGE_EMAIL_BACKEND=resend
AVATARFORGE_EMAIL_VERIFICATION_REQUIRED=1
AVATARFORGE_EMAIL_FROM=onboarding@resend.dev
RESEND_API_KEY=...
```

For a real production launch, use a verified custom sending domain.

---

# Private Generation History

Signed-in users can save completed generations to their private account history.

Routes:

```text
/generations
/generations/<generation-id>/image
```

Generated files are not exposed as public static assets.

---

# Developer API

AvatarForge includes a developer-facing API layer.

Users can:

- create API keys
- list API keys
- revoke API keys
- inspect usage
- call generation APIs programmatically

API keys use the format:

```text
af_live_...
```

Keys are shown only once.

Only SHA-256 hashes are stored in the database.

Send keys using:

```http
Authorization: Bearer af_live_...
```

Developer routes include:

```text
GET    /api/v1/developer/keys
POST   /api/v1/developer/keys
DELETE /api/v1/developer/keys/<key-id>
GET    /api/v1/developer/usage
```

---

# Usage Quotas

The developer platform supports:

- monthly generation quotas
- API usage tracking
- per-minute rate limiting
- plan-based limits

---

# Rate Limiting

Supported rate-limit backends:

```text
memory
redis
```

## Local

```text
AVATARFORGE_RATE_LIMIT_BACKEND=memory
```

## Distributed Production

```text
AVATARFORGE_RATE_LIMIT_BACKEND=redis
REDIS_URL=...
```

---

# Plans and Billing

AvatarForge includes:

- Free plan
- Pro plan
- Business plan
- monthly usage dashboard
- subscription persistence
- plan-aware usage limits
- mock billing mode
- Stripe-ready billing integration

Account routes include:

```text
/account/billing
/account/settings
```

Billing routes include:

```text
/account/billing/checkout/<plan-code>
/account/billing/portal
/api/v1/billing/webhook
```

---

# Billing Providers

## Mock Billing

Default for development and demos:

```text
AVATARFORGE_BILLING_PROVIDER=mock
```

Allows plan upgrades without charging real money.

## Stripe

Production billing can be enabled with:

```text
AVATARFORGE_BILLING_PROVIDER=stripe
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
```

Additional Stripe price IDs and production app URL must also be configured.

---

# Storage Architecture

AvatarForge uses a storage abstraction instead of hardcoding filesystem operations.

Supported backends:

```text
local
s3
```

## Local Storage

Suitable for:

- local development
- testing
- temporary Vercel demo execution

```text
AVATARFORGE_STORAGE_BACKEND=local
```

## S3-Compatible Storage

Production-ready object storage:

```text
AVATARFORGE_STORAGE_BACKEND=s3
AVATARFORGE_S3_BUCKET=...
AVATARFORGE_S3_PREFIX=avatarforge
AVATARFORGE_S3_REGION=us-east-1
AVATARFORGE_S3_ENDPOINT_URL=
AVATARFORGE_S3_ACCESS_KEY_ID=...
AVATARFORGE_S3_SECRET_ACCESS_KEY=...
```

Generated objects are private.

AvatarForge serves them through authenticated or token-protected application routes rather than exposing public bucket URLs.

S3 uploads support server-side encryption using:

```text
AES256
```

---

# Retry Policy

Generation jobs support automatic retries.

Default:

```text
AVATARFORGE_JOB_MAX_ATTEMPTS=2
```

Each job tracks:

```text
attempt_count
max_attempts
```

Temporary source inputs remain available during retries and are cleaned after jobs reach a terminal state.

---

# Lifecycle Cleanup

Old terminal job data can be removed using:

```powershell
python maintenance.py cleanup-jobs
```

Custom retention:

```powershell
python maintenance.py cleanup-jobs --older-than-hours 48
```

Default:

```text
AVATARFORGE_JOB_RETENTION_HOURS=24
```

Saved account history is not deleted by job cleanup.

---

# Observability

AvatarForge includes production observability features.

## Request IDs

Each API response can include:

```text
X-Request-ID
```

Clients may also provide their own request IDs.

## Structured Logging

Enable JSON logs with:

```text
AVATARFORGE_JSON_LOGS=1
AVATARFORGE_LOG_LEVEL=INFO
```

Useful for:

- Vercel Runtime Logs
- centralized observability
- production troubleshooting

## Prometheus Metrics

AvatarForge exposes metrics for:

- request counts
- request latency
- generation success
- generation failures
- job retries
- active jobs

Endpoint:

```text
GET /api/v1/metrics
```

---

# Database

AvatarForge uses:

- SQLAlchemy 2
- SQLite for local development
- PostgreSQL for production
- Psycopg 3
- Alembic migrations

## Local Database

Default:

```text
instance/avatarforge.db
```

## Production Database

Production uses:

```text
DATABASE_URL
```

A managed PostgreSQL database is recommended.

The current Vercel deployment uses Neon PostgreSQL.

---

# Database Migrations

Run:

```powershell
python -m alembic upgrade head
```

Current migration sequence includes:

```text
0001_accounts_generations
0002_generation_jobs
0003_job_retry_fields
0004_developer_api_keys
0005_billing_subscriptions
0006_email_verification
```

---

# Production Database Safeguards

AvatarForge prevents accidental SQLite usage in production when PostgreSQL is required.

Automated tests are exempt from the production-only PostgreSQL restriction.

PostgreSQL engines use:

- connection health checks
- connection recycling
- rollback on request teardown errors
- serverless-safe pooling mode where configured

---

# Security

AvatarForge includes:

- password hashing
- CSRF protection
- secure sessions
- email verification
- password-reset tokens
- private generation access
- anonymous job tokens
- API key hashing
- signed verification links
- signed password reset links
- CSP headers
- HSTS in secure production
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
- safe proxy handling

---

# Security Headers

Production responses include security headers such as:

```text
Content-Security-Policy
Strict-Transport-Security
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Permissions-Policy
```

---

# AI Provider Architecture

AvatarForge separates generation logic from provider-specific implementation.

Available providers:

```text
mock
fal
remote
```

## Mock Provider

```powershell
$env:AVATARFORGE_AI_PROVIDER="mock"
python app.py
```

Useful without external credentials.

## fal.ai

```powershell
$env:AVATARFORGE_AI_PROVIDER="fal"
$env:FAL_KEY="your-key"
python app.py
```

Never commit API keys.

---

# Local Development

Clone the repository:

```bash
git clone https://github.com/prajwal-devaraj/avatarforge-ai.git
cd avatarforge-ai
```

Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest -q
```

Run the application:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
http://127.0.0.1:5000/studio
```

---

# Recommended Local Environment

```powershell
$env:AVATARFORGE_AI_PROVIDER="mock"
$env:AVATARFORGE_JOB_BACKEND="thread"
$env:AVATARFORGE_STORAGE_BACKEND="local"
$env:AVATARFORGE_RATE_LIMIT_BACKEND="memory"
$env:AVATARFORGE_BILLING_PROVIDER="mock"
$env:AVATARFORGE_EMAIL_BACKEND="console"
$env:AVATARFORGE_EMAIL_VERIFICATION_REQUIRED="0"

python app.py
```

---

# Testing

AvatarForge has automated coverage across:

- Flask application routes
- API contracts
- image processing
- authentication
- private generation history
- AI provider abstraction
- fal.ai provider
- asynchronous jobs
- retries
- storage
- observability
- developer API
- API keys
- quotas
- billing
- account settings
- email verification
- password reset
- Vercel adaptation

Current validated suite:

```text
39 passed
```

---

# Docker

AvatarForge includes:

```text
Dockerfile
docker-compose.yml
docker/entrypoint.sh
docker/worker-entrypoint.sh
```

The Docker architecture supports:

- Flask / Gunicorn web process
- PostgreSQL
- Redis
- RQ worker
- Alembic migrations
- shared private generation storage

Start locally:

```bash
docker compose up --build
```

---

# Production Runtime

Outside Docker:

```bash
alembic upgrade head

gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 4 \
  --timeout 180 \
  wsgi:app
```

---

# Vercel Deployment

AvatarForge is deployed on Vercel using native Flask support.

Current production URL:

```text
https://avatarforge-ai.vercel.app
```

The deployment architecture uses:

```text
GitHub
   |
   v
Vercel
   |
   +--> Flask Application
   |
   +--> Neon PostgreSQL
   |
   +--> Temporary / External Storage
   |
   +--> Resend Email
   |
   +--> Optional fal.ai Provider
```

---

# Current Vercel Demo Configuration

For the demo deployment:

```text
AVATARFORGE_JOB_BACKEND=inline
AVATARFORGE_STORAGE_BACKEND=local
AVATARFORGE_RATE_LIMIT_BACKEND=memory
AVATARFORGE_BILLING_PROVIDER=mock
```

This configuration is suitable for demonstrating the product.

For long-term production, durable object storage and distributed rate limiting should be used.

---

# Vercel Environment Variables

Important production variables include:

```text
DATABASE_URL
AVATARFORGE_SECRET_KEY

AVATARFORGE_JOB_BACKEND
AVATARFORGE_STORAGE_BACKEND

AVATARFORGE_AI_PROVIDER
FAL_KEY

AVATARFORGE_RATE_LIMIT_BACKEND
REDIS_URL

AVATARFORGE_EMAIL_BACKEND
AVATARFORGE_EMAIL_FROM
AVATARFORGE_EMAIL_VERIFICATION_REQUIRED
RESEND_API_KEY

AVATARFORGE_BILLING_PROVIDER
```

Never commit production secrets.

---

# Technology Stack

## Backend
- Python
- Flask
- SQLAlchemy 2
- Alembic
- Psycopg 3

## Computer Vision
- OpenCV
- Pillow
- NumPy

## AI
- fal.ai
- provider abstraction
- image-to-image generation
- prompt-driven generation

## Database
- SQLite
- PostgreSQL
- Neon

## Queue and Background Processing
- thread worker
- inline execution
- Redis
- RQ

## Storage
- local filesystem abstraction
- S3-compatible storage
- private generated objects

## Developer Platform
- versioned REST API
- API keys
- quotas
- rate limiting
- usage tracking

## Observability
- Prometheus
- structured JSON logging
- health checks
- readiness checks
- correlation IDs

## Security
- Werkzeug password hashing
- CSRF protection
- signed tokens
- email verification
- password reset
- security headers

## Billing
- mock billing
- Stripe-ready architecture

## Deployment
- Docker
- Gunicorn
- GitHub
- Vercel
- Neon PostgreSQL

## Frontend
- HTML
- CSS
- JavaScript
- responsive SaaS UI

## Testing
- Pytest

---

# Engineering Evolution

AvatarForge was intentionally built incrementally.

The project evolved through:

1. local Flask + OpenCV avatar prototype
2. premium product landing page
3. dedicated Avatar Studio
4. multiple image transformation styles
5. modular service architecture
6. versioned API contracts
7. authentication and persistent history
8. generative AI provider abstraction
9. fal.ai integration
10. asynchronous generation jobs
11. Docker and production runtime
12. storage lifecycle and observability
13. developer API keys, quotas and rate limiting
14. billing plans and account management
15. account security and password recovery
16. Vercel serverless adaptation
17. live deployment with Neon PostgreSQL

---

# Design Philosophy

## Build the product, not only the model

AI generation is only one part of a usable AI product.

The platform also needs:

- identity
- persistence
- security
- billing
- developer access
- storage
- observability
- deployment
- reliability

## Provider Independence

AI providers change quickly.

AvatarForge isolates provider logic so models and vendors can change without redesigning the whole application.

## Privacy by Default

Generated images are treated as private user data rather than public static assets.

## Local Development Should Stay Simple

The platform can run with:

- SQLite
- local storage
- mock AI
- in-memory rate limiting
- thread workers

without requiring cloud infrastructure.

## Production Infrastructure Should Scale Independently

Database, storage, queueing, AI providers, billing, and email can each be replaced or scaled independently.

---

# Current Status

AvatarForge AI currently has:

- live Vercel deployment
- working Classic avatar generation
- Neon PostgreSQL production database
- production database migrations
- authentication
- email verification architecture
- password recovery
- generation history
- developer APIs
- API keys
- quotas
- billing infrastructure
- observability
- Docker deployment support
- 39 passing automated tests

AI generation through fal.ai is supported by the architecture and can be enabled by configuring production provider credentials.

---

# Future Roadmap

Potential next improvements:

- real production fal.ai generation
- durable cloud object storage
- production Redis rate limiting
- external async worker infrastructure
- Stripe live billing
- verified custom email domain
- team accounts
- organization workspaces
- avatar collections
- additional AI styles
- 3D avatar generation
- identity consistency across generations
- mobile experience
- admin analytics
- usage dashboards
- developer SDKs
- webhooks
- enterprise controls

---

# Author

**Prajwal Devaraj**

Software Engineer | AI/ML Engineer | Backend & Full-Stack Developer | AI Agents, LLMs & RAG | Researcher

GitHub:  
https://github.com/prajwal-devaraj

---

# License

This repository is currently maintained as an experimental product and portfolio project.

Before commercial distribution, add an explicit software license appropriate for the intended business model.

---

# Final Note

AvatarForge AI started as a simple computer-vision experiment and evolved into an end-to-end AI SaaS platform.

The goal was not only to generate an avatar.

The goal was to understand and build the complete engineering system required to turn an AI capability into a usable product:

```text
AI
+
Backend Engineering
+
Security
+
Cloud Infrastructure
+
APIs
+
Data
+
Observability
+
Product Experience
=
AvatarForge AI
```
