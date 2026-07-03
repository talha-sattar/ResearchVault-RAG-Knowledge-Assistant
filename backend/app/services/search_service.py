import uuid

from sqlalchemy.orm import Session

from app.db.enums import SearchType
from app.db.models import Document, SearchHistory, User
from app.retrieval.retriever import retrieve


def search_papers(
    db: Session, user: User, query: str, top_k: int = 10, category: str | None = None
) -> list[dict]:
    # Over-fetch chunks since several may map to the same document; we want top_k *documents*.
    chunks = retrieve(db, query, top_k=top_k * 3)

    seen_docs: set[str] = set()
    results: list[dict] = []
    for c in chunks:
        if c.document_id in seen_docs:
            continue
        doc = db.get(Document, uuid.UUID(c.document_id))
        if doc is None:
            continue
        if category and doc.primary_category != category:
            continue
        seen_docs.add(c.document_id)
        results.append(
            {
                "document": doc,
                "snippet": c.content[:300],
                "section_type": c.section_type,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "score": c.rerank_score,
            }
        )
        if len(results) >= top_k:
            break

    db.add(
        SearchHistory(
            user_id=user.id,
            query_text=query,
            search_type=SearchType.HYBRID,
            result_document_ids=list(seen_docs),
        )
    )
    db.commit()
    return results
