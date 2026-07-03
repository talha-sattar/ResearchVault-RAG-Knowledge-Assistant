from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.document import DocumentSummary
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.search_service import search_papers

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    body: SearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SearchResponse:
    results = search_papers(db, user, body.query, top_k=body.top_k, category=body.category)
    return SearchResponse(
        query=body.query,
        results=[
            SearchResultItem(
                document=DocumentSummary.model_validate(r["document"]),
                snippet=r["snippet"],
                section_type=r["section_type"],
                page_start=r["page_start"],
                page_end=r["page_end"],
                score=r["score"],
            )
            for r in results
        ],
    )
