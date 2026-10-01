#!/bin/sh
set -eu

if [ "${AVATARFORGE_RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Applying database migrations..."
  alembic upgrade head
fi

exec gunicorn \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-180}" \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
