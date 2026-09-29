from app.providers.base import BaseLLMProvider
from app.providers.gemini_provider import gemini_provider, GeminiProvider
from app.providers.openai_provider import openai_provider, OpenAIProvider

def get_llm_provider(provider_name: str = "gemini") -> BaseLLMProvider:
    if provider_name.lower() == "openai":
        return openai_provider
    return gemini_provider

__all__ = [
    "BaseLLMProvider",
    "GeminiProvider",
    "gemini_provider",
    "OpenAIProvider",
    "openai_provider",
    "get_llm_provider",
]
