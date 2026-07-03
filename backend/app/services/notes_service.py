import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import User, UserNote


def create_note(db: Session, user: User, document_id: uuid.UUID, content: str, page_reference: int | None) -> UserNote:
    note = UserNote(user_id=user.id, document_id=document_id, content=content, page_reference=page_reference)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_notes_for_document(db: Session, user: User, document_id: uuid.UUID) -> list[UserNote]:
    return (
        db.query(UserNote)
        .filter(UserNote.user_id == user.id, UserNote.document_id == document_id)
        .order_by(UserNote.created_at.desc())
        .all()
    )


def update_note(db: Session, user: User, note_id: uuid.UUID, content: str, page_reference: int | None) -> UserNote:
    note = db.query(UserNote).filter(UserNote.id == note_id, UserNote.user_id == user.id).one_or_none()
    if note is None:
        raise NotFoundError("Note", note_id)
    note.content = content
    note.page_reference = page_reference
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, user: User, note_id: uuid.UUID) -> None:
    note = db.query(UserNote).filter(UserNote.id == note_id, UserNote.user_id == user.id).one_or_none()
    if note is None:
        raise NotFoundError("Note", note_id)
    db.delete(note)
    db.commit()
