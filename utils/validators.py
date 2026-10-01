from typing import Any


ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MIN_INTENSITY = 10
MAX_INTENSITY = 100
DEFAULT_INTENSITY = 70


def clamp_intensity(raw_value: str | None) -> int:
    """Normalize a user-provided style intensity into a supported range."""
    try:
        value = int(raw_value or DEFAULT_INTENSITY)
    except (TypeError, ValueError):
        value = DEFAULT_INTENSITY
    return max(MIN_INTENSITY, min(MAX_INTENSITY, value))


def validate_upload(file_storage: Any | None) -> None:
    """Validate that a file was supplied before image decoding begins."""
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise ValueError("Please choose an image first.")
