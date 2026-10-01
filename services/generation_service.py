from dataclasses import dataclass

from PIL import UnidentifiedImageError

from services.image_service import STYLE_LABELS, apply_style, prepare_image
from utils.image_utils import encode_jpeg
from utils.validators import clamp_intensity, validate_upload


@dataclass(frozen=True)
class GenerationResult:
    image_stream: object
    style: str
    style_label: str
    intensity: int
    download_name: str


def generate_avatar(file_storage, raw_style: str | None, raw_intensity: str | None) -> GenerationResult:
    """Orchestrate validation, decoding, style processing, and output encoding."""
    validate_upload(file_storage)

    style = (raw_style or "cartoon").strip().lower()
    if style not in STYLE_LABELS:
        raise ValueError("That style is not supported.")

    intensity = clamp_intensity(raw_intensity)

    try:
        source = prepare_image(file_storage)
    except UnidentifiedImageError as exc:
        raise ValueError("Please upload a valid JPG, PNG, or WEBP image.") from exc

    result = apply_style(source, style, intensity)
    stream = encode_jpeg(result)

    return GenerationResult(
        image_stream=stream,
        style=style,
        style_label=STYLE_LABELS[style],
        intensity=intensity,
        download_name=f"avatarforge-{style.replace('_', '-')}.jpg",
    )
