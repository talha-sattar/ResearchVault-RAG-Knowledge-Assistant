import uuid

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models import CollectionDocument, User, UserCollection


def create_collection(db: Session, user: User, name: str, description: str | None) -> UserCollection:
    collection = UserCollection(user_id=user.id, name=name, description=description)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def list_collections(db: Session, user: User) -> list[UserCollection]:
    return db.query(UserCollection).filter(UserCollection.user_id == user.id).order_by(UserCollection.created_at.desc()).all()


def get_collection(db: Session, user: User, collection_id: uuid.UUID) -> UserCollection:
    collection = (
        db.query(UserCollection)
        .options(joinedload(UserCollection.documents).joinedload(CollectionDocument.document))
        .filter(UserCollection.id == collection_id, UserCollection.user_id == user.id)
        .one_or_none()
    )
    if collection is None:
        raise NotFoundError("Collection", collection_id)
    return collection


def add_document(db: Session, user: User, collection_id: uuid.UUID, document_id: uuid.UUID) -> None:
    get_collection(db, user, collection_id)  # ownership + existence check
    exists = (
        db.query(CollectionDocument)
        .filter(CollectionDocument.collection_id == collection_id, CollectionDocument.document_id == document_id)
        .one_or_none()
    )
    if exists is None:
        db.add(CollectionDocument(collection_id=collection_id, document_id=document_id))
        db.commit()


def remove_document(db: Session, user: User, collection_id: uuid.UUID, document_id: uuid.UUID) -> None:
    get_collection(db, user, collection_id)
    db.query(CollectionDocument).filter(
        CollectionDocument.collection_id == collection_id, CollectionDocument.document_id == document_id
    ).delete()
    db.commit()


def delete_collection(db: Session, user: User, collection_id: uuid.UUID) -> None:
    collection = get_collection(db, user, collection_id)
    db.delete(collection)
    db.commit()
