import uuid
from datetime import datetime

from sqlalchemy import (
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import (
    AnswerFormat,
    ChunkingStrategy,
    ChunkLevel,
    ConversationScope,
    DocumentSource,
    MessageRole,
    ParseStatus,
    SearchType,
    SectionType,
    ViewType,
)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _enum_col(py_enum, **kw):
    from sqlalchemy import Enum as SAEnum

    # values_callable: store enum .value ("parent_child") not .name ("PARENT_CHILD") so the
    # DB text matches Python .value, JSON/API responses, and the Chroma metadata we write
    # alongside it (indexer.py stores c.chunk_level.value etc there).
    return mapped_column(
        SAEnum(py_enum, native_enum=False, validate_strings=True, values_callable=lambda e: [m.value for m in e]),
        **kw,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    collections: Mapped[list["UserCollection"]] = relationship(back_populates="user")
    notes: Mapped[list["UserNote"]] = relationship(back_populates="user")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    preferences: Mapped["UserPreference | None"] = relationship(back_populates="user", uselist=False)
    search_history: Mapped[list["SearchHistory"]] = relationship(back_populates="user")
    document_views: Mapped[list["DocumentView"]] = relationship(back_populates="user")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[uuid.UUID] = _uuid_pk()
    full_name: Mapped[str] = mapped_column(String(500))
    normalized_name: Mapped[str] = mapped_column(String(500), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["DocumentAuthor"]] = relationship(back_populates="author")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    arxiv_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    primary_category: Mapped[str | None] = mapped_column(String(50), index=True)
    categories: Mapped[list[str]] = mapped_column(JSONB, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pdf_url: Mapped[str | None] = mapped_column(Text)
    abs_url: Mapped[str | None] = mapped_column(Text)
    pdf_local_path: Mapped[str | None] = mapped_column(Text)
    parse_status: Mapped[ParseStatus] = _enum_col(ParseStatus, default=ParseStatus.PENDING)
    chunking_strategy: Mapped[ChunkingStrategy | None] = _enum_col(ChunkingStrategy, nullable=True)
    source: Mapped[DocumentSource] = _enum_col(DocumentSource, default=DocumentSource.ARXIV)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    authors: Mapped[list["DocumentAuthor"]] = relationship(back_populates="document", order_by="DocumentAuthor.author_order")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_documents_primary_category", "primary_category"),)


class DocumentAuthor(Base):
    __tablename__ = "document_authors"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)
    author_order: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["Document"] = relationship(back_populates="authors")
    author: Mapped["Author"] = relationship(back_populates="documents")


class DocumentChunk(Base):
    """Primary key doubles as the Chroma vector id - no separate mapping table."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunking_strategy: Mapped[ChunkingStrategy] = _enum_col(ChunkingStrategy)
    chunk_level: Mapped[ChunkLevel] = _enum_col(ChunkLevel, default=ChunkLevel.LEAF)
    parent_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True, nullable=True
    )
    section_type: Mapped[SectionType] = _enum_col(SectionType, default=SectionType.OTHER)
    content: Mapped[str] = mapped_column(Text)
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True)
    )
    token_count: Mapped[int | None] = mapped_column(Integer)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    char_start: Mapped[int | None] = mapped_column(Integer)
    char_end: Mapped[int | None] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="chunks")
    parent: Mapped["DocumentChunk | None"] = relationship(remote_side=[id])

    __table_args__ = (
        Index("ix_document_chunks_section_type", "section_type"),
        Index("ix_document_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
    )


class UserCollection(Base):
    __tablename__ = "user_collections"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="collections")
    documents: Mapped[list["CollectionDocument"]] = relationship(back_populates="collection", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_collection_name"),)


class CollectionDocument(Base):
    __tablename__ = "collection_documents"

    collection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_collections.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    collection: Mapped["UserCollection"] = relationship(back_populates="documents")
    document: Mapped["Document"] = relationship()


class UserNote(Base):
    __tablename__ = "user_notes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    page_reference: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="notes")
    document: Mapped["Document"] = relationship()

    __table_args__ = (Index("ix_user_notes_user_document", "user_id", "document_id"),)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    scope: Mapped[ConversationScope] = _enum_col(ConversationScope, default=ConversationScope.GENERAL)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    documents: Mapped[list["ConversationDocument"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class ConversationDocument(Base):
    __tablename__ = "conversation_documents"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="documents")
    document: Mapped["Document"] = relationship()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[MessageRole] = _enum_col(MessageRole)
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    retrieved_chunk_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    provider_used: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    token_usage: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    favorite_categories: Mapped[list[str]] = mapped_column(JSONB, default=list)
    preferred_answer_format: Mapped[AnswerFormat] = _enum_col(AnswerFormat, default=AnswerFormat.CONCISE)
    default_top_k: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="preferences")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    search_type: Mapped[SearchType] = _enum_col(SearchType, default=SearchType.HYBRID)
    result_document_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    clicked_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="search_history")

    __table_args__ = (Index("ix_search_history_user_created", "user_id", "created_at"),)


class DocumentView(Base):
    """Reading-history signal feeding the recommender's engagement-weighted centroid."""

    __tablename__ = "document_views"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    view_type: Mapped[ViewType] = _enum_col(ViewType)
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    user: Mapped["User"] = relationship(back_populates="document_views")
    document: Mapped["Document"] = relationship()

    __table_args__ = (
        Index("ix_document_views_user_document", "user_id", "document_id"),
        Index("ix_document_views_user_viewed", "user_id", "viewed_at"),
    )
