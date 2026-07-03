from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

EMBED_BATCH_SIZE = 100


def _client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)


@retry(reraise=True, stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
def _embed_batch(client: OpenAI, model: str, batch: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=batch)
    return [item.embedding for item in response.data]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """OpenAI text-embedding-3-small only - no live cross-provider fallback (see plan:
    Gemini/OpenAI embeddings are different, incompatible vector spaces for one Chroma index)."""
    if not texts:
        return []
    settings = get_settings()
    client = _client()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        vectors.extend(_embed_batch(client, settings.openai_embedding_model, batch))
    return vectors
