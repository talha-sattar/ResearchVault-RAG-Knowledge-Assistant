import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import DocumentChunk
from app.ingestion.embedding import embed_texts
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.keyword_search import keyword_search
from app.retrieval.reranker import rerank
from app.retrieval.vector_store import dense_search

DENSE_K = 20
SPARSE_K = 20
RERANK_CANDIDATES = 30
DEFAULT_TOP_K = 6


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    arxiv_id: str | None
    title: str
    section_type: str
    page_start: int | None
    page_end: int | None
    content: str
    parent_content: str | None
    rerank_score: float


def retrieve(
    db: Session,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    document_ids: list[uuid.UUID] | None = None,
) -> list[RetrievedChunk]:
    """Full hybrid pipeline: dense (Chroma) + sparse (Postgres FTS) -> Reciprocal Rank
    Fusion -> cross-encoder rerank -> top_k chunks with parent context attached."""
    query_embedding = embed_texts([query])[0]

    doc_id_strs = [str(d) for d in document_ids] if document_ids else None
    dense_results = dense_search(query_embedding, top_k=DENSE_K, document_ids=doc_id_strs)
    sparse_results = keyword_search(db, query, top_k=SPARSE_K, document_ids=document_ids)

    dense_ranking = [chunk_id for chunk_id, _ in dense_results]
    sparse_ranking = [chunk_id for chunk_id, _ in sparse_results]
    fused = reciprocal_rank_fusion([dense_ranking, sparse_ranking])[:RERANK_CANDIDATES]
    fused_ids = [chunk_id for chunk_id, _ in fused]
    if not fused_ids:
        return []

    rows = (
        db.execute(
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.document), joinedload(DocumentChunk.parent))
            .where(DocumentChunk.id.in_([uuid.UUID(cid) for cid in fused_ids]))
        )
        .unique()
        .scalars()
        .all()
    )
    rows_by_id = {str(row.id): row for row in rows}

    candidates = [(chunk_id, rows_by_id[chunk_id].content) for chunk_id in fused_ids if chunk_id in rows_by_id]
    reranked = rerank(query, candidates, top_k=top_k)

    results = []
    for chunk_id, score in reranked:
        row = rows_by_id[chunk_id]
        results.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                document_id=str(row.document_id),
                arxiv_id=row.document.arxiv_id,
                title=row.document.title,
                section_type=row.section_type.value,
                page_start=row.page_start,
                page_end=row.page_end,
                content=row.content,
                parent_content=row.parent.content if row.parent else None,
                rerank_score=score,
            )
        )
    return results
