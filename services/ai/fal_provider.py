from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from .base import AIImageResult


class FalAIProvider:
    """fal.ai image-to-image provider using FLUX.1 Kontext [pro].

    The provider is server-side only. It uploads the user's temporary source image
    to fal storage, submits an image edit request, downloads the generated image,
    and returns bytes to the existing AvatarForge pipeline.
    """

    name = "fal"
    model = "fal-ai/flux-pro/kontext"

    def __init__(self, api_key: str, timeout: int = 120):
        self.api_key = (api_key or "").strip()
        self.timeout = int(timeout)
        if not self.api_key:
            raise ValueError(
                "fal.ai is not configured. Set FAL_KEY, or use mock/classic mode."
            )

    def generate(
        self,
        *,
        image_bytes: bytes,
        filename: str,
        mime_type: str,
        prompt: str,
        style: str,
        intensity: int,
    ) -> AIImageResult:
        try:
            import fal_client
        except ImportError as exc:
            raise RuntimeError(
                "fal-client is not installed. Run: python -m pip install -r requirements.txt"
            ) from exc

        # fal-client reads FAL_KEY from the process environment.
        os.environ["FAL_KEY"] = self.api_key

        suffix = Path(filename or "upload.jpg").suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                handle.write(image_bytes)
                temp_path = handle.name

            image_url = fal_client.upload_file(temp_path)
            result = fal_client.subscribe(
                self.model,
                arguments={
                    "prompt": prompt,
                    "image_url": image_url,
                    "num_images": 1,
                    "output_format": "jpeg",
                    "enhance_prompt": True,
                },
            )
        except Exception as exc:
            raise RuntimeError(f"fal.ai generation failed: {exc}") from exc
        finally:
            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except OSError:
                    pass

        images = result.get("images") if isinstance(result, dict) else None
        if not images or not isinstance(images, list) or not images[0].get("url"):
            raise RuntimeError("fal.ai returned no generated image.")

        output_url = images[0]["url"]
        content_type = images[0].get("content_type") or "image/jpeg"
        request = Request(output_url, headers={"User-Agent": "AvatarForgeAI/1.0"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                output_bytes = response.read()
                response_type = response.headers.get_content_type()
        except Exception as exc:
            raise RuntimeError(f"Could not download fal.ai output: {exc}") from exc

        if not output_bytes:
            raise RuntimeError("fal.ai returned an empty image.")

        return AIImageResult(
            image_bytes=output_bytes,
            mime_type=response_type or content_type,
            provider=self.name,
        )
