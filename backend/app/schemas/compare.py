import uuid

from pydantic import BaseModel

from app.schemas.citation import AnswerOut


class CompareRequest(BaseModel):
    document_ids: list[uuid.UUID]
    aspect: str | None = None


class CompareResponse(BaseModel):
    answer: AnswerOut
