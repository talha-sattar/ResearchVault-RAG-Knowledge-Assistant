import logging
from functools import lru_cache

from app.core.exceptions import LLMProviderError
from app.llm.providers.base import ChatMessage, GenerationResult, LLMProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


@lru_cache
def _providers() -> list[LLMProvider]:
    # OpenAI primary, Gemini fallback on error/rate-limit. Generation-only fallback is safe
    # (text-in/text-out); embeddings intentionally do NOT get this treatment - see embedding.py.
    return [OpenAIProvider(), GeminiProvider()]


def generate(
    messages: list[ChatMessage],
    *,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> GenerationResult:
    last_error: Exception | None = None
    for provider in _providers():
        try:
            return provider.generate(messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as exc:
            logger.warning("LLM provider %s failed: %s", provider.name, exc)
            last_error = exc
    raise LLMProviderError(f"All LLM providers failed. Last error: {last_error}")
