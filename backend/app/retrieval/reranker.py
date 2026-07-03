from functools import lru_cache

from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache
def _get_model() -> CrossEncoder:
    return CrossEncoder(MODEL_NAME)


def rerank(query: str, candidates: list[tuple[str, str]], top_k: int = 8) -> list[tuple[str, float]]:
    """candidates: [(chunk_id, chunk_text), ...] -> top_k (chunk_id, cross_encoder_score),
    sorted best first. Runs after RRF fusion, right before chunks go into the LLM prompt."""
    if not candidates:
        return []
    pairs = [(query, text) for _, text in candidates]
    scores = _get_model().predict(pairs)
    ranked = sorted(zip((c[0] for c in candidates), scores), key=lambda pair: pair[1], reverse=True)
    return [(chunk_id, float(score)) for chunk_id, score in ranked[:top_k]]
