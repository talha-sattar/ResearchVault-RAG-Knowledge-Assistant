import logging

from sqlalchemy.orm import Session

from app.db.enums import DocumentSource, ParseStatus
from app.db.models import Author, Document, DocumentAuthor
from app.ingestion.arxiv_client import ArxivPaper
from app.ingestion.utils import normalize_author_name

logger = logging.getLogger(__name__)


def _get_or_create_author(db: Session, full_name: str) -> Author:
    normalized = normalize_author_name(full_name)
    author = db.query(Author).filter(Author.normalized_name == normalized).one_or_none()
    if author is None:
        author = Author(full_name=full_name, normalized_name=normalized)
        db.add(author)
        db.flush()
    return author


def upsert_paper(db: Session, paper: ArxivPaper) -> Document:
    """Create (or merge categories into) a Document row + its author links. Does not download/parse the PDF."""
    document = db.query(Document).filter(Document.arxiv_id == paper.arxiv_id).one_or_none()

    if document is not None:
        merged_categories = sorted(set(document.categories) | set(paper.categories))
        if merged_categories != document.categories:
            document.categories = merged_categories
        return document

    document = Document(
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        abstract=paper.abstract,
        primary_category=paper.primary_category,
        categories=paper.categories,
        published_at=paper.published_at,
        pdf_url=paper.pdf_url,
        abs_url=paper.abs_url,
        parse_status=ParseStatus.PENDING,
        source=DocumentSource.ARXIV,
    )
    db.add(document)
    db.flush()

    for order, author_name in enumerate(paper.authors):
        author = _get_or_create_author(db, author_name)
        db.add(DocumentAuthor(document_id=document.id, author_id=author.id, author_order=order))

    return document
