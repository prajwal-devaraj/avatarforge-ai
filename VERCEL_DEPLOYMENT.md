# AvatarForge AI — Vercel Deployment

AvatarForge is prepared for Vercel's Python runtime through `api/index.py` and `vercel.json`.

## Production architecture

- **Web/API:** Vercel Python Function running Flask/WSGI.
- **Database:** managed PostgreSQL. Neon is available directly through the Vercel Marketplace.
- **Generated media/job inputs:** S3-compatible durable object storage. Local function disk is not treated as durable storage.
- **AI:** fal.ai or another remote provider.
- **Email:** Resend HTTP API.
- **Rate limiting:** Redis-compatible service when you need distributed enforcement.
- **Job execution:** `inline` on Vercel by default. This keeps work inside the request lifecycle and does not depend on a permanent thread/RQ worker. If generation grows beyond Vercel Function execution limits, move job execution to an external worker or a Vercel Workflow/Queue-based design.

## Required production environment variables

Set these in Vercel Project > Settings > Environment Variables:

```text
AVATARFORGE_ENV=production
AVATARFORGE_SECRET_KEY=<long-random-secret>
DATABASE_URL=<managed-postgres-connection-string>
AVATARFORGE_REQUIRE_POSTGRES_IN_PRODUCTION=1
AVATARFORGE_DB_POOL_MODE=serverless

AVATARFORGE_AI_PROVIDER=fal
FAL_KEY=<fal-key>

AVATARFORGE_JOB_BACKEND=inline
AVATARFORGE_STORAGE_BACKEND=s3
AVATARFORGE_S3_BUCKET=<bucket>
AVATARFORGE_S3_PREFIX=avatarforge
AVATARFORGE_S3_REGION=<region>
AVATARFORGE_S3_ENDPOINT_URL=<optional-for-S3-compatible-provider>
AVATARFORGE_S3_ACCESS_KEY_ID=<key-id>
AVATARFORGE_S3_SECRET_ACCESS_KEY=<secret>
AVATARFORGE_S3_SSE=AES256

AVATARFORGE_EMAIL_BACKEND=resend
AVATARFORGE_EMAIL_FROM=<verified-sender>
RESEND_API_KEY=<resend-key>
AVATARFORGE_EMAIL_VERIFICATION_REQUIRED=1

AVATARFORGE_BILLING_PROVIDER=mock
AVATARFORGE_APP_BASE_URL=https://<your-vercel-domain>

AVATARFORGE_JSON_LOGS=1
AVATARFORGE_TRUST_PROXY_HEADERS=1
AVATARFORGE_SESSION_COOKIE_SECURE=1
```

When Stripe is enabled later, switch `AVATARFORGE_BILLING_PROVIDER=stripe` and add the Stripe secrets/price IDs.

## Database migration

Do not rely on `Base.metadata.create_all()` in production. `ProductionConfig` keeps automatic creation disabled.

Before the first live production request, run Alembic against the production `DATABASE_URL` from a trusted local terminal or CI job:

```powershell
$env:DATABASE_URL="<production-postgres-url>"
python -m alembic upgrade head
```

Repeat `alembic upgrade head` whenever a deployment contains a new migration.

## Vercel import

1. In Vercel, choose **Add New > Project**.
2. Import `prajwal-devaraj/avatarforge-ai` from GitHub.
3. Keep the repository root as the Root Directory.
4. Vercel reads `vercel.json` and routes requests to `api/index.py`.
5. Add the production environment variables above.
6. Provision/connect PostgreSQL and object storage before generating avatars.
7. Deploy.

## Smoke checks

After deployment verify:

```text
/
/studio
/api/v1/health
/api/v1/ready
/auth/register
/auth/forgot-password
```

Then create a test account, generate one avatar, verify private history, test email verification/reset, and inspect Vercel Function logs.

## Serverless behavior

`VERCEL=1` is detected automatically. If `AVATARFORGE_ENV` is omitted, AvatarForge selects production configuration. The Vercel defaults are intentionally conservative:

- job backend: `inline`
- storage backend: `s3`
- trusted proxy headers: enabled
- JSON logs: enabled
- PostgreSQL pool mode: `serverless` (`NullPool`)

These can still be overridden through explicit environment variables.
