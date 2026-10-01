from io import BytesIO
from PIL import Image, ImageEnhance
from .base import AIImageResult

class MockAIProvider:
    name="mock"
    def generate(self, *, image_bytes: bytes, filename: str, mime_type: str, prompt: str, style: str, intensity: int) -> AIImageResult:
        image=Image.open(BytesIO(image_bytes)).convert("RGB")
        image=ImageEnhance.Color(image).enhance(1.15)
        out=BytesIO(); image.save(out,format="JPEG",quality=92)
        return AIImageResult(out.getvalue(),"image/jpeg",self.name)
