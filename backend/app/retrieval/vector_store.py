from app.core.chroma_client import get_production_collection


def dense_search(
    query_embedding: list[float],
    top_k: int = 20,
    document_ids: list[str] | None = None,
) -> list[tuple[str, float]]:
    """Chroma cosine search over the production collection (leaf/child chunks only -
    those are the only vectors ever written there, see indexer.py). Returns (chunk_id, distance)."""
    collection = get_production_collection()
    where = {"document_id": {"$in": document_ids}} if document_ids else None
    result = collection.query(query_embeddings=[query_embedding], n_results=top_k, where=where)

    ids = result["ids"][0] if result["ids"] else []
    distances = result["distances"][0] if result["distances"] else []
    return list(zip(ids, distances))
