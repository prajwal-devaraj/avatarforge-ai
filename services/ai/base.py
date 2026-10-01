from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AIImageResult:
    image_bytes: bytes
    mime_type: str
    provider: str

class AIProvider(Protocol):
    name: str
    def generate(self, *, image_bytes: bytes, filename: str, mime_type: str, prompt: str, style: str, intensity: int) -> AIImageResult: ...
