import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.citation import CitationOut


class ChatRequest(BaseModel):
    question: str
    document_ids: list[uuid.UUID] | None = None
    conversation_id: uuid.UUID | None = None


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationOut]
    created_at: datetime


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageOut


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str | None
    scope: str
    created_at: datetime
    updated_at: datetime
