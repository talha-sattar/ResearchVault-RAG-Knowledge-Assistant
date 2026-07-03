import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.collection import AddDocumentRequest, CollectionCreate, CollectionOut, CollectionWithDocuments
from app.schemas.document import DocumentSummary
from app.services import collections_service

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionOut)
def create_collection(
    body: CollectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CollectionOut:
    collection = collections_service.create_collection(db, user, body.name, body.description)
    return CollectionOut(
        id=collection.id, name=collection.name, description=collection.description, created_at=collection.created_at
    )


@router.get("", response_model=list[CollectionOut])
def list_collections(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[CollectionOut]:
    collections = collections_service.list_collections(db, user)
    return [
        CollectionOut(id=c.id, name=c.name, description=c.description, created_at=c.created_at, document_count=len(c.documents))
        for c in collections
    ]


@router.get("/{collection_id}", response_model=CollectionWithDocuments)
def get_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CollectionWithDocuments:
    collection = collections_service.get_collection(db, user, collection_id)
    documents = [DocumentSummary.model_validate(cd.document) for cd in collection.documents]
    return CollectionWithDocuments(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        document_count=len(documents),
        documents=documents,
    )


@router.post("/{collection_id}/documents", status_code=204)
def add_document(
    collection_id: uuid.UUID,
    body: AddDocumentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    collections_service.add_document(db, user, collection_id, body.document_id)


@router.delete("/{collection_id}/documents/{document_id}", status_code=204)
def remove_document(
    collection_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    collections_service.remove_document(db, user, collection_id, document_id)


@router.delete("/{collection_id}", status_code=204)
def delete_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    collections_service.delete_collection(db, user, collection_id)
