#!/bin/sh
set -eu

exec rq worker \
  --url "${REDIS_URL:-redis://redis:6379/0}" \
  "${AVATARFORGE_RQ_QUEUE:-avatarforge}"
