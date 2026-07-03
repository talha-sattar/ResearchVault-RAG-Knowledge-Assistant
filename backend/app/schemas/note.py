import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    document_id: uuid.UUID
    content: str
    page_reference: int | None = None


class NoteUpdate(BaseModel):
    content: str
    page_reference: int | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    content: str
    page_reference: int | None
    created_at: datetime
    updated_at: datetime
