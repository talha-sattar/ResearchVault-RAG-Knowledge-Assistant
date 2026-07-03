import uuid

from sqlalchemy.orm import Session, joinedload

from app.db.enums import ViewType
from app.db.models import Document, DocumentView, User
from app.llm.generation import AnswerResult, generate_answer
from app.llm.prompts import extract_task, summarize_task
from app.retrieval.representative import representative_chunks_for_document


def get_document(db: Session, document_id: uuid.UUID) -> Document | None:
    return (
        db.query(Document)
        .options(joinedload(Document.authors))
        .filter(Document.id == document_id)
        .one_or_none()
    )


def list_documents(db: Session, category: str | None = None, limit: int = 50, offset: int = 0) -> list[Document]:
    query = db.query(Document)
    if category:
        query = query.filter(Document.primary_category == category)
    return query.order_by(Document.published_at.desc()).offset(offset).limit(limit).all()


def summarize_document(db: Session, document_id: uuid.UUID, answer_format: str = "concise") -> AnswerResult:
    chunks = representative_chunks_for_document(db, document_id, per_section=1, max_total=6)
    return generate_answer(summarize_task(), chunks, answer_format=answer_format)


def extract_document(db: Session, document_id: uuid.UUID) -> AnswerResult:
    chunks = representative_chunks_for_document(db, document_id, per_section=2, max_total=10)
    return generate_answer(extract_task(), chunks, answer_format="detailed")


def log_view(db: Session, user: User, document_id: uuid.UUID, view_type: ViewType) -> None:
    db.add(DocumentView(user_id=user.id, document_id=document_id, view_type=view_type))
    db.commit()
