import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthorOut(BaseModel):
    full_name: str


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    arxiv_id: str | None
    title: str
    primary_category: str | None
    categories: list[str]
    published_at: datetime | None
    abs_url: str | None


class DocumentOut(DocumentSummary):
    abstract: str | None
    pdf_url: str | None
    authors: list[str] = []

    @classmethod
    def from_orm_with_authors(cls, doc) -> "DocumentOut":
        return cls(
            id=doc.id,
            arxiv_id=doc.arxiv_id,
            title=doc.title,
            abstract=doc.abstract,
            primary_category=doc.primary_category,
            categories=doc.categories,
            published_at=doc.published_at,
            abs_url=doc.abs_url,
            pdf_url=doc.pdf_url,
            authors=[da.author.full_name for da in doc.authors],
        )
