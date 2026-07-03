import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.enums import ChunkLevel
from app.db.models import DocumentChunk


def keyword_search(
    db: Session,
    query: str,
    top_k: int = 20,
    document_ids: list[uuid.UUID] | None = None,
) -> list[tuple[str, float]]:
    """Postgres full-text search (sparse leg of hybrid retrieval) over leaf/child chunks
    only, using the GIN-indexed content_tsv column. Returns (chunk_id, ts_rank_cd score)."""
    tsquery = func.plainto_tsquery("english", query)
    rank = func.ts_rank_cd(DocumentChunk.content_tsv, tsquery).label("rank")

    stmt = (
        select(DocumentChunk.id, rank)
        .where(DocumentChunk.content_tsv.op("@@")(tsquery))
        .where(DocumentChunk.chunk_level.in_([ChunkLevel.LEAF, ChunkLevel.CHILD]))
    )
    if document_ids:
        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
    stmt = stmt.order_by(rank.desc()).limit(top_k)

    rows = db.execute(stmt).all()
    return [(str(chunk_id), score) for chunk_id, score in rows]
