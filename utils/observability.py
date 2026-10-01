from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

from flask import g, request
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "avatarforge_http_requests_total",
    "HTTP requests handled by AvatarForge AI",
    ["method", "endpoint", "status"],
)
HTTP_LATENCY = Histogram(
    "avatarforge_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)
GENERATION_JOBS = Counter(
    "avatarforge_generation_jobs_total",
    "Generation jobs by terminal outcome",
    ["status", "engine", "provider"],
)
GENERATION_LATENCY = Histogram(
    "avatarforge_generation_duration_seconds",
    "Generation processing latency",
    ["engine", "provider"],
)
JOB_RETRIES = Counter(
    "avatarforge_generation_job_retries_total",
    "Generation job retry attempts",
    ["engine"],
)
ACTIVE_JOBS = Gauge(
    "avatarforge_generation_jobs_active",
    "Currently processing generation jobs",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(g, "request_id", None) if _has_request_context() else None
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _has_request_context() -> bool:
    try:
        from flask import has_request_context

        return has_request_context()
    except RuntimeError:
        return False


def configure_json_logging(app) -> None:
    if not app.config.get("JSON_LOGS", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO))


def mark_request_start() -> None:
    g._request_started_at = time.perf_counter()


def observe_response(response):
    started = getattr(g, "_request_started_at", None)
    endpoint = request.endpoint or "unknown"
    HTTP_REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
    if started is not None:
        HTTP_LATENCY.labels(request.method, endpoint).observe(max(0.0, time.perf_counter() - started))
    return response
