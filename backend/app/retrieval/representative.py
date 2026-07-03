import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.enums import ChunkLevel
from app.db.models import Document, DocumentChunk
from app.retrieval.retriever import RetrievedChunk

# Preferred order when picking representative sections - not every paper has all of these.
PRIORITY_SECTIONS = ["abstract", "introduction", "methodology", "experiments", "results", "conclusion"]


def representative_chunks_for_document(
    db: Session, document_id: uuid.UUID, per_section: int = 1, max_total: int = 8
) -> list[RetrievedChunk]:
    """Summarize/extract/compare have no natural free-text query to run similarity search
    against, so instead pull a representative spread of child chunks across section types
    directly from Postgres."""
    doc = db.get(Document, document_id)
    if doc is None:
        return []

    rows = (
        db.execute(
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.parent))
            .where(DocumentChunk.document_id == document_id)
            .where(DocumentChunk.chunk_level == ChunkLevel.CHILD)
            .order_by(DocumentChunk.chunk_index)
        )
        .scalars()
        .all()
    )

    by_section: dict[str, list[DocumentChunk]] = {}
    for row in rows:
        by_section.setdefault(row.section_type.value, []).append(row)

    selected: list[DocumentChunk] = []
    for section in PRIORITY_SECTIONS:
        selected.extend(by_section.get(section, [])[:per_section])
    for row in rows:
        if len(selected) >= max_total:
            break
        if row not in selected:
            selected.append(row)
    selected = selected[:max_total]

    return [
        RetrievedChunk(
            chunk_id=str(row.id),
            document_id=str(row.document_id),
            arxiv_id=doc.arxiv_id,
            title=doc.title,
            section_type=row.section_type.value,
            page_start=row.page_start,
            page_end=row.page_end,
            content=row.content,
            parent_content=row.parent.content if row.parent else None,
            rerank_score=0.0,
        )
        for row in selected
    ]


def representative_chunks_for_documents(
    db: Session, document_ids: list[uuid.UUID], per_section: int = 1, max_per_doc: int = 6
) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []
    for doc_id in document_ids:
        chunks.extend(representative_chunks_for_document(db, doc_id, per_section=per_section, max_total=max_per_doc))
    return chunks
