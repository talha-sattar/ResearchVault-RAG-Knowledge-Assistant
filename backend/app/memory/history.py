from sqlalchemy.orm import Session, joinedload

from app.db.models import DocumentView, SearchHistory, User


def list_search_history(db: Session, user: User, limit: int = 50) -> list[SearchHistory]:
    return (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
        .all()
    )


def list_document_views(db: Session, user: User, limit: int = 50) -> list[DocumentView]:
    return (
        db.query(DocumentView)
        .options(joinedload(DocumentView.document))
        .filter(DocumentView.user_id == user.id)
        .order_by(DocumentView.viewed_at.desc())
        .limit(limit)
        .all()
    )
