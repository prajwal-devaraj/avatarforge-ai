from flask import current_app

from .fal_provider import FalAIProvider
from .mock_provider import MockAIProvider
from .remote_provider import RemoteAIProvider


def get_ai_provider():
    provider = current_app.config.get("AI_PROVIDER", "remote").strip().lower()

    if provider == "mock":
        return MockAIProvider()

    if provider == "fal":
        return FalAIProvider(
            current_app.config.get("FAL_KEY", ""),
            current_app.config.get("AI_TIMEOUT", 120),
        )

    if provider == "remote":
        endpoint = current_app.config.get("AI_ENDPOINT", "").strip()
        if not endpoint:
            raise ValueError(
                "Remote AI generation is not configured. Set AVATARFORGE_AI_ENDPOINT, "
                "choose AVATARFORGE_AI_PROVIDER=fal with FAL_KEY, or use mock/classic mode."
            )
        return RemoteAIProvider(
            endpoint,
            current_app.config.get("AI_API_KEY", ""),
            current_app.config.get("AI_TIMEOUT", 120),
        )

    raise ValueError(
        "Unknown AI provider. Use mock, fal, or remote."
    )
