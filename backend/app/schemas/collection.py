import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.document import DocumentSummary


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None


class CollectionOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    document_count: int = 0


class CollectionWithDocuments(CollectionOut):
    documents: list[DocumentSummary]


class AddDocumentRequest(BaseModel):
    document_id: uuid.UUID
