from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.citation import AnswerOut, CitationOut
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.compare_service import compare_documents

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
def compare(body: CompareRequest, db: Session = Depends(get_db)) -> CompareResponse:
    result = compare_documents(db, body.document_ids, aspect=body.aspect)
    return CompareResponse(
        answer=AnswerOut(
            text=result.text,
            citations=[CitationOut(**vars(c)) for c in result.citations],
            is_refusal=result.is_refusal,
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms,
        )
    )
