"""Production indexing: parses + chunks each ingested paper using the winning chunking
strategy from experiments/chunking/REPORT.md, writes DocumentChunk rows to Postgres, and
embeds/upserts the searchable (leaf/child) chunks into the production Chroma collection.

Usage:
    python -m app.ingestion.indexer [--limit N] [--reindex]
"""

import argparse
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.chroma_client import get_production_collection
from app.core.logging import setup_logging
from app.db.base import SessionLocal
from app.db.enums import ChunkingStrategy, ChunkLevel, ParseStatus
from app.db.models import Document, DocumentChunk
from app.ingestion.chunkers import CHUNKERS
from app.ingestion.embedding import embed_texts
from app.ingestion.pdf_parser import parse_pdf

logger = logging.getLogger(__name__)

# Winner of the 4-way comparison in experiments/chunking/REPORT.md (effective-context
# Recall@5 = 0.90 vs 0.77-0.83 for the other strategies).
PRODUCTION_STRATEGY = ChunkingStrategy.PARENT_CHILD

CHROMA_WRITE_BATCH = 100


def _clear_existing_chunks(db: Session, collection, document: Document) -> None:
    existing = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
    if not existing:
        return
    try:
        collection.delete(ids=[str(c.id) for c in existing])
    except Exception:
        logger.debug("Nothing to delete in Chroma for %s (fine on first index)", document.arxiv_id)
    for c in existing:
        db.delete(c)
    db.flush()


def index_document(db: Session, collection, document: Document, strategy: ChunkingStrategy = PRODUCTION_STRATEGY) -> int:
    pdf_path = Path(document.pdf_local_path) if document.pdf_local_path else None
    if pdf_path is None or not pdf_path.exists():
        logger.warning("Skipping %s: no PDF on disk", document.arxiv_id)
        return 0

    parsed = parse_pdf(pdf_path)
    document.parse_status = parsed.parse_status
    if parsed.parse_status != ParseStatus.PARSED:
        db.commit()
        logger.warning("Skipping %s: parse_status=%s", document.arxiv_id, parsed.parse_status.value)
        return 0

    _clear_existing_chunks(db, collection, document)

    chunks = CHUNKERS[strategy].chunk(parsed)
    if not chunks:
        db.commit()
        logger.warning("Skipping %s: chunker produced no chunks", document.arxiv_id)
        return 0

    # Pass 1: insert every chunk row so each gets a DB-assigned UUID.
    rows_by_local_index: dict[int, DocumentChunk] = {}
    for i, c in enumerate(chunks):
        row = DocumentChunk(
            document_id=document.id,
            chunking_strategy=strategy,
            chunk_level=c.chunk_level,
            section_type=c.section_type,
            content=c.content,
            token_count=c.token_count,
            page_start=c.page_start,
            page_end=c.page_end,
            char_start=c.char_start,
            char_end=c.char_end,
            chunk_index=c.chunk_index,
        )
        db.add(row)
        rows_by_local_index[i] = row
    db.flush()  # assigns .id to every row above

    # Pass 2: now that parent rows have DB ids, wire up children's parent_chunk_id FK.
    for i, c in enumerate(chunks):
        if c.parent_index is not None:
            rows_by_local_index[i].parent_chunk_id = rows_by_local_index[c.parent_index].id

    # Only leaf/child chunks are searchable units; parents exist for context-expansion only.
    embeddable = [(i, c) for i, c in enumerate(chunks) if c.chunk_level in (ChunkLevel.LEAF, ChunkLevel.CHILD)]
    settings = get_settings()
    embeddings = embed_texts([c.content for _, c in embeddable])

    chroma_ids, chroma_docs, chroma_metas, chroma_embeds = [], [], [], []
    for (i, c), vector in zip(embeddable, embeddings):
        row = rows_by_local_index[i]
        row.embedding_model = settings.openai_embedding_model
        chroma_ids.append(str(row.id))
        chroma_docs.append(c.content)
        chroma_metas.append(
            {
                "document_id": str(document.id),
                "arxiv_id": document.arxiv_id or "",
                "section_type": c.section_type.value,
                "chunk_level": c.chunk_level.value,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "chunking_strategy": strategy.value,
            }
        )
        chroma_embeds.append(vector)

    for i in range(0, len(chroma_ids), CHROMA_WRITE_BATCH):
        collection.add(
            ids=chroma_ids[i : i + CHROMA_WRITE_BATCH],
            embeddings=chroma_embeds[i : i + CHROMA_WRITE_BATCH],
            documents=chroma_docs[i : i + CHROMA_WRITE_BATCH],
            metadatas=chroma_metas[i : i + CHROMA_WRITE_BATCH],
        )

    document.chunking_strategy = strategy
    db.commit()
    return len(chunks)


def run(limit: int | None, reindex: bool) -> None:
    collection = get_production_collection()
    db = SessionLocal()
    total_chunks = 0
    documents = []
    try:
        query = select(Document).where(Document.pdf_local_path.is_not(None))
        if not reindex:
            query = query.where(Document.chunking_strategy.is_(None))
        if limit:
            query = query.limit(limit)
        documents = db.execute(query).scalars().all()
        logger.info("Indexing %d documents with strategy=%s", len(documents), PRODUCTION_STRATEGY.value)

        for i, document in enumerate(documents, start=1):
            total_chunks += index_document(db, collection, document)
            if i % 10 == 0 or i == len(documents):
                logger.info("Progress: %d/%d documents, %d chunks so far", i, len(documents), total_chunks)
    finally:
        db.close()

    logger.info("Indexing complete: %d documents, %d chunks, collection=%s", len(documents), total_chunks, collection.name)


def main():
    parser = argparse.ArgumentParser(description="Index ingested papers into Postgres document_chunks + Chroma.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--reindex", action="store_true", help="Re-index documents that already have a chunking_strategy set"
    )
    args = parser.parse_args()
    setup_logging()
    run(args.limit, args.reindex)


if __name__ == "__main__":
    main()
