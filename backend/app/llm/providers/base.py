from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str
    token_usage: dict = field(default_factory=dict)


class LLMProvider(ABC):
    """Common interface implemented by each backing model provider (OpenAI, Gemini, ...)."""

    name: str

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> GenerationResult:
        ...


class EmbeddingProvider(ABC):
    """Separate from LLMProvider: embeddings must stay on one provider per index (see router.py)."""

    name: str
    dimensions: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...
