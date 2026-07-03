from pydantic import BaseModel

from app.schemas.document import DocumentSummary


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    category: str | None = None


class SearchResultItem(BaseModel):
    document: DocumentSummary
    snippet: str
    section_type: str
    page_start: int | None
    page_end: int | None
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]


class RecommendationItem(BaseModel):
    document: DocumentSummary
    reason: str
    score: float
