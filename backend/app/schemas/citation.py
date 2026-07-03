from pydantic import BaseModel


class CitationOut(BaseModel):
    doc_index: int
    chunk_id: str
    document_id: str
    arxiv_id: str | None
    page: int | None
    marker_text: str


class AnswerOut(BaseModel):
    text: str
    citations: list[CitationOut]
    is_refusal: bool
    provider: str
    model: str
    latency_ms: int
