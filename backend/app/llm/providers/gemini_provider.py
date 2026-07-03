from google import genai
from google.genai import types

from app.config import get_settings
from app.llm.providers.base import ChatMessage, GenerationResult, LLMProvider


class GeminiProvider(LLMProvider):
    """Fallback generation provider only (see plan: embeddings must stay single-provider,
    but text generation is safe to fall back between providers)."""

    name = "gemini"

    def __init__(self):
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_chat_model

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> GenerationResult:
        system_parts = [m.content for m in messages if m.role == "system"]
        contents = [
            types.Content(role="model" if m.role == "assistant" else "user", parts=[types.Part(text=m.content)])
            for m in messages
            if m.role != "system"
        ]
        config = types.GenerateContentConfig(
            system_instruction="\n\n".join(system_parts) or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = self._client.models.generate_content(model=self._model, contents=contents, config=config)
        usage = response.usage_metadata
        return GenerationResult(
            text=response.text or "",
            provider=self.name,
            model=self._model,
            token_usage=(
                {
                    "prompt_tokens": usage.prompt_token_count,
                    "completion_tokens": usage.candidates_token_count,
                }
                if usage
                else {}
            ),
        )
