from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.chat import ChatRequest, ChatResponse, MessageOut
from app.schemas.citation import CitationOut
from app.services.chat_service import ask

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    conversation, message = ask(
        db,
        user,
        question=body.question,
        document_ids=body.document_ids,
        conversation_id=body.conversation_id,
    )
    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageOut(
            id=message.id,
            role=message.role.value,
            content=message.content,
            citations=[CitationOut(**c) for c in message.citations],
            created_at=message.created_at,
        ),
    )
