from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from flask import current_app


def _backend() -> str:
    return str(current_app.config.get("STORAGE_BACKEND", "local")).strip().lower()


def _s3_client():
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for S3 storage.") from exc

    kwargs = {}
    endpoint = current_app.config.get("S3_ENDPOINT_URL")
    region = current_app.config.get("S3_REGION")
    access_key = current_app.config.get("S3_ACCESS_KEY_ID")
    secret_key = current_app.config.get("S3_SECRET_ACCESS_KEY")
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    if region:
        kwargs["region_name"] = region
    if access_key:
        kwargs["aws_access_key_id"] = access_key
    if secret_key:
        kwargs["aws_secret_access_key"] = secret_key
    return boto3.client("s3", **kwargs)


def _s3_object_key(category: str, key: str) -> str:
    prefix = str(current_app.config.get("S3_PREFIX", "avatarforge")).strip("/")
    parts = [part for part in (prefix, category.strip("/"), key.strip("/")) if part]
    return "/".join(parts)


def store_bytes(*, category: str, key: str, data: bytes, mime_type: str = "application/octet-stream") -> str:
    """Store bytes and return a durable storage location string.

    Local storage returns a filesystem path for backward compatibility.
    S3-compatible storage returns an s3://bucket/key URI.
    """
    backend = _backend()
    if backend == "local":
        root_config = "GENERATED_STORAGE_DIR" if category == "generations" else "JOB_STORAGE_DIR"
        root = Path(current_app.config[root_config])
        path = root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    if backend == "s3":
        bucket = str(current_app.config.get("S3_BUCKET", "")).strip()
        if not bucket:
            raise RuntimeError("S3_BUCKET must be configured when STORAGE_BACKEND=s3.")
        object_key = _s3_object_key(category, key)
        _s3_client().put_object(
            Bucket=bucket,
            Key=object_key,
            Body=data,
            ContentType=mime_type,
            ServerSideEncryption=current_app.config.get("S3_SERVER_SIDE_ENCRYPTION", "AES256"),
        )
        return f"s3://{bucket}/{object_key}"

    raise RuntimeError(f"Unsupported storage backend: {backend}")


def read_bytes(location: str) -> bytes:
    if location.startswith("s3://"):
        parsed = urlparse(location)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        response = _s3_client().get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    return Path(location).read_bytes()


def delete_location(location: str | None) -> bool:
    if not location:
        return False
    try:
        if location.startswith("s3://"):
            parsed = urlparse(location)
            _s3_client().delete_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
            return True
        Path(location).unlink(missing_ok=True)
        return True
    except Exception:
        current_app.logger.exception("Could not delete storage object %s", location)
        return False


def location_exists(location: str | None) -> bool:
    if not location:
        return False
    if location.startswith("s3://"):
        parsed = urlparse(location)
        try:
            _s3_client().head_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
            return True
        except Exception:
            return False
    return Path(location).is_file()


def storage_ready() -> tuple[bool, str]:
    backend = _backend()
    try:
        if backend == "local":
            Path(current_app.config["JOB_STORAGE_DIR"]).mkdir(parents=True, exist_ok=True)
            return True, "local"
        if backend == "s3":
            bucket = current_app.config.get("S3_BUCKET")
            if not bucket:
                return False, "S3_BUCKET is not configured"
            _s3_client().head_bucket(Bucket=bucket)
            return True, "s3"
        return False, f"unsupported backend: {backend}"
    except Exception as exc:
        return False, str(exc)
