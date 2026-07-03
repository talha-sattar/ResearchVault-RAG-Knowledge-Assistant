import uuid
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.enums import ConversationScope, MessageRole
from app.db.models import Conversation, ConversationDocument, Message, User, UserPreference
from app.llm.generation import generate_answer
from app.retrieval.retriever import retrieve


def _resolve_answer_format(db: Session, user: User) -> str:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user.id).one_or_none()
    return pref.preferred_answer_format.value if pref else "concise"


def ask(
    db: Session,
    user: User,
    question: str,
    document_ids: list[uuid.UUID] | None = None,
    conversation_id: uuid.UUID | None = None,
) -> tuple[Conversation, Message]:
    if conversation_id is not None:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation", conversation_id)
        if document_ids is None:
            # Continuing a conversation without re-specifying scope: stay scoped to
            # whichever papers it was originally created against, otherwise a follow-up
            # question silently falls back to a corpus-wide search and drifts off-topic.
            existing = (
                db.query(ConversationDocument.document_id)
                .filter(ConversationDocument.conversation_id == conversation.id)
                .all()
            )
            if existing:
                document_ids = [row[0] for row in existing]
    else:
        if document_ids and len(document_ids) == 1:
            scope = ConversationScope.SINGLE_PAPER
        elif document_ids:
            scope = ConversationScope.MULTI_PAPER
        else:
            scope = ConversationScope.GENERAL
        conversation = Conversation(user_id=user.id, title=question[:80], scope=scope)
        db.add(conversation)
        db.flush()
        for doc_id in document_ids or []:
            db.add(ConversationDocument(conversation_id=conversation.id, document_id=doc_id))

    db.add(Message(conversation_id=conversation.id, role=MessageRole.USER, content=question))
    db.flush()

    answer_format = _resolve_answer_format(db, user)
    chunks = retrieve(db, question, top_k=6, document_ids=document_ids)
    result = generate_answer(question, chunks, answer_format=answer_format)

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=result.text,
        citations=[asdict(c) for c in result.citations],
        retrieved_chunk_ids=result.retrieved_chunk_ids,
        provider_used=result.provider,
        model_name=result.model,
        latency_ms=result.latency_ms,
        token_usage=result.token_usage,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    db.refresh(conversation)
    return conversation, assistant_message
