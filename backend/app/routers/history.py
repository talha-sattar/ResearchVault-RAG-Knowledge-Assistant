from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.memory import history as history_module

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/search")
def search_history(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    rows = history_module.list_search_history(db, user, limit=limit)
    return [
        {
            "id": str(r.id),
            "query_text": r.query_text,
            "search_type": r.search_type.value,
            "result_document_ids": r.result_document_ids,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/views")
def document_views(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    rows = history_module.list_document_views(db, user, limit=limit)
    return [
        {
            "id": str(r.id),
            "document_id": str(r.document_id),
            "view_type": r.view_type.value,
            "viewed_at": r.viewed_at.isoformat(),
        }
        for r in rows
    ]
