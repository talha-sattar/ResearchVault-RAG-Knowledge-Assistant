from openai import OpenAI

from app.config import get_settings
from app.llm.providers.base import ChatMessage, GenerationResult, LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self):
        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> GenerationResult:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = response.usage
        return GenerationResult(
            text=response.choices[0].message.content or "",
            provider=self.name,
            model=self._model,
            token_usage=(
                {"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens}
                if usage
                else {}
            ),
        )
