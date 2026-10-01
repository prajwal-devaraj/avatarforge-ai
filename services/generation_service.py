from dataclasses import dataclass
from io import BytesIO
from PIL import UnidentifiedImageError
from services.ai import get_ai_provider
from services.image_service import STYLE_LABELS, apply_style, prepare_image
from services.prompt_service import build_prompt
from utils.image_utils import encode_jpeg
from utils.validators import clamp_intensity, validate_upload

@dataclass(frozen=True)
class GenerationResult:
    image_stream: object
    style: str
    style_label: str
    intensity: int
    download_name: str
    engine: str = "classic"
    provider: str = "opencv"
    prompt: str = ""

def generate_avatar(file_storage, raw_style: str|None, raw_intensity: str|None, raw_engine: str|None="classic", raw_prompt: str|None=None) -> GenerationResult:
    validate_upload(file_storage)
    style=(raw_style or "cartoon").strip().lower()
    if style not in STYLE_LABELS: raise ValueError("That style is not supported.")
    intensity=clamp_intensity(raw_intensity)
    engine=(raw_engine or "classic").strip().lower()
    if engine not in {"classic","ai"}: raise ValueError("Generation mode must be classic or ai.")
    if engine=="ai":
        data=file_storage.read(); file_storage.stream.seek(0)
        prompt=build_prompt(raw_prompt,style,intensity)
        provider=get_ai_provider()
        result=provider.generate(image_bytes=data,filename=file_storage.filename or "upload.jpg",mime_type=file_storage.mimetype or "image/jpeg",prompt=prompt,style=style,intensity=intensity)
        return GenerationResult(BytesIO(result.image_bytes),style,STYLE_LABELS[style],intensity,f"avatarforge-ai-{style}.jpg","ai",result.provider,prompt)
    try:
        source=prepare_image(file_storage)
    except UnidentifiedImageError as exc:
        raise ValueError("Please upload a valid JPG, PNG, or WEBP image.") from exc
    out=apply_style(source,style,intensity)
    return GenerationResult(encode_jpeg(out),style,STYLE_LABELS[style],intensity,f"avatarforge-{style.replace('_','-')}.jpg")
