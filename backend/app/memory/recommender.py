import uuid

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.chroma_client import get_production_collection
from app.db.enums import ChunkLevel
from app.db.models import Document, DocumentChunk

CENTROID_SAMPLE_CHUNKS = 8


def similar_documents(db: Session, document_id: uuid.UUID, top_k: int = 5) -> list[tuple[Document, float]]:
    """Baseline "related papers": nearest documents by cosine distance to this paper's own
    embedding centroid. Task-level personalization (weighting by the user's reading/search
    history) is layered on top in recommend_for_user, not here."""
    collection = get_production_collection()

    chunk_ids = (
        db.execute(
            select(DocumentChunk.id)
            .where(DocumentChunk.document_id == document_id)
            .where(DocumentChunk.chunk_level == ChunkLevel.CHILD)
            .limit(CENTROID_SAMPLE_CHUNKS)
        )
        .scalars()
        .all()
    )
    if not chunk_ids:
        return []

    got = collection.get(ids=[str(cid) for cid in chunk_ids], include=["embeddings"])
    embeddings = got.get("embeddings")
    if embeddings is None or len(embeddings) == 0:
        return []
    centroid = np.mean(np.array(embeddings), axis=0).tolist()

    return _nearest_documents_to_vector(db, centroid, exclude_document_ids={document_id}, top_k=top_k)


def _nearest_documents_to_vector(
    db: Session, vector: list[float], exclude_document_ids: set[uuid.UUID], top_k: int
) -> list[tuple[Document, float]]:
    collection = get_production_collection()
    exclude_strs = {str(d) for d in exclude_document_ids}

    # Exclude the source document(s) directly in the query - a document's own chunks are
    # near-guaranteed to be the nearest neighbors of its own centroid, so filtering only
    # after over-fetching (as a first pass did) can come back empty for any real corpus size.
    where = {"document_id": {"$nin": list(exclude_strs)}} if exclude_strs else None
    result = collection.query(query_embeddings=[vector], n_results=top_k * 6, where=where)

    best_distance_by_doc: dict[str, float] = {}
    ids = result["ids"][0] if result["ids"] else []
    distances = result["distances"][0] if result["distances"] else []
    metadatas = result["metadatas"][0] if result["metadatas"] else []
    for _, distance, meta in zip(ids, distances, metadatas):
        doc_id = meta["document_id"]
        if doc_id not in best_distance_by_doc or distance < best_distance_by_doc[doc_id]:
            best_distance_by_doc[doc_id] = distance

    ranked = sorted(best_distance_by_doc.items(), key=lambda pair: pair[1])[:top_k]
    results = []
    for doc_id_str, distance in ranked:
        doc = db.get(Document, uuid.UUID(doc_id_str))
        if doc is not None:
            results.append((doc, max(0.0, 1.0 - distance)))
    return results
