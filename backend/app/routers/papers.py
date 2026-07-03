import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.enums import ViewType
from app.db.models import User
from app.memory.recommender import similar_documents
from app.schemas.citation import AnswerOut, CitationOut
from app.schemas.document import DocumentOut, DocumentSummary
from app.schemas.search import RecommendationItem
from app.services import papers_service

router = APIRouter(prefix="/papers", tags=["papers"])


def _answer_to_schema(result) -> AnswerOut:
    return AnswerOut(
        text=result.text,
        citations=[CitationOut(**vars(c)) for c in result.citations],
        is_refusal=result.is_refusal,
        provider=result.provider,
        model=result.model,
        latency_ms=result.latency_ms,
    )


@router.get("", response_model=list[DocumentSummary])
def list_papers(
    category: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[DocumentSummary]:
    docs = papers_service.list_documents(db, category=category, limit=limit, offset=offset)
    return [DocumentSummary.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentOut)
def get_paper(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentOut:
    doc = papers_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    papers_service.log_view(db, user, document_id, ViewType.DETAIL_OPEN)
    return DocumentOut.from_orm_with_authors(doc)


@router.post("/{document_id}/summarize", response_model=AnswerOut)
def summarize_paper(
    document_id: uuid.UUID,
    answer_format: str = "concise",
    db: Session = Depends(get_db),
) -> AnswerOut:
    if papers_service.get_document(db, document_id) is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    result = papers_service.summarize_document(db, document_id, answer_format=answer_format)
    return _answer_to_schema(result)


@router.post("/{document_id}/extract", response_model=AnswerOut)
def extract_paper(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> AnswerOut:
    if papers_service.get_document(db, document_id) is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    result = papers_service.extract_document(db, document_id)
    return _answer_to_schema(result)


@router.get("/{document_id}/related", response_model=list[RecommendationItem])
def related_papers(
    document_id: uuid.UUID,
    top_k: int = Query(5, le=20),
    db: Session = Depends(get_db),
) -> list[RecommendationItem]:
    if papers_service.get_document(db, document_id) is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    pairs = similar_documents(db, document_id, top_k=top_k)
    return [
        RecommendationItem(document=DocumentSummary.model_validate(doc), reason="Similar content", score=score)
        for doc, score in pairs
    ]
