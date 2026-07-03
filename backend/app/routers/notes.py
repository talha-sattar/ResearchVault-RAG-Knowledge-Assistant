import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services import notes_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteOut)
def create_note(
    body: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NoteOut:
    note = notes_service.create_note(db, user, body.document_id, body.content, body.page_reference)
    return NoteOut.model_validate(note)


@router.get("/document/{document_id}", response_model=list[NoteOut])
def list_notes(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[NoteOut]:
    notes = notes_service.list_notes_for_document(db, user, document_id)
    return [NoteOut.model_validate(n) for n in notes]


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: uuid.UUID,
    body: NoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NoteOut:
    note = notes_service.update_note(db, user, note_id, body.content, body.page_reference)
    return NoteOut.model_validate(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    notes_service.delete_note(db, user, note_id)
