"""
AI Service Abstraction Package for InternTrack AI
"""
from .base import BaseAIProvider
from .gemini_provider import GeminiAIProvider
from .nlp_fallback_provider import LocalNLPFallbackProvider

def get_ai_provider() -> BaseAIProvider:
    """
    Factory function returning GeminiAIProvider if GEMINI_API_KEY is configured,
    otherwise returning the deterministic LocalNLPFallbackProvider.
    """
    from django.conf import settings
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if api_key and api_key.strip():
        try:
            return GeminiAIProvider(api_key=api_key.strip(), model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash'))
        except Exception:
            # Graceful fallback to local NLP if provider initialization fails
            return LocalNLPFallbackProvider()
    return LocalNLPFallbackProvider()

__all__ = ['BaseAIProvider', 'GeminiAIProvider', 'LocalNLPFallbackProvider', 'get_ai_provider']
