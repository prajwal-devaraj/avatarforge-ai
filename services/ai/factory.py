from flask import current_app
from .mock_provider import MockAIProvider
from .remote_provider import RemoteAIProvider

def get_ai_provider():
    provider=current_app.config.get("AI_PROVIDER","remote").lower()
    if provider=="mock": return MockAIProvider()
    endpoint=current_app.config.get("AI_ENDPOINT","").strip()
    if not endpoint: raise ValueError("AI generation is not configured. Set AVATARFORGE_AI_ENDPOINT or use Classic mode.")
    return RemoteAIProvider(endpoint,current_app.config.get("AI_API_KEY",""),current_app.config.get("AI_TIMEOUT",60))
