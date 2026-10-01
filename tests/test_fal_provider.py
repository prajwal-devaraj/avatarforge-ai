import sys
import types

import pytest

from services.ai.fal_provider import FalAIProvider


def test_fal_provider_requires_key():
    with pytest.raises(ValueError, match="FAL_KEY"):
        FalAIProvider("")


def test_fal_provider_uses_upload_and_kontext(monkeypatch, tmp_path):
    calls = {}

    fake = types.SimpleNamespace()

    def upload_file(path):
        calls["upload_path"] = path
        return "https://example.test/input.jpg"

    def subscribe(model, arguments):
        calls["model"] = model
        calls["arguments"] = arguments
        return {
            "images": [
                {
                    "url": "https://example.test/output.jpg",
                    "content_type": "image/jpeg",
                }
            ]
        }

    fake.upload_file = upload_file
    fake.subscribe = subscribe
    monkeypatch.setitem(sys.modules, "fal_client", fake)

    class Headers:
        @staticmethod
        def get_content_type():
            return "image/jpeg"

    class Response:
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @staticmethod
        def read():
            return b"generated-image"

    monkeypatch.setattr("services.ai.fal_provider.urlopen", lambda *args, **kwargs: Response())

    provider = FalAIProvider("test-key")
    result = provider.generate(
        image_bytes=b"input-image",
        filename="avatar.jpg",
        mime_type="image/jpeg",
        prompt="Turn this into a polished founder portrait",
        style="soft_portrait",
        intensity=80,
    )

    assert calls["model"] == "fal-ai/flux-pro/kontext"
    assert calls["arguments"]["image_url"] == "https://example.test/input.jpg"
    assert calls["arguments"]["prompt"].startswith("Turn this")
    assert result.image_bytes == b"generated-image"
    assert result.provider == "fal"
