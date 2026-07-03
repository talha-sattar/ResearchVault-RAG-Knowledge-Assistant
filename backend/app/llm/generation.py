import re
import time
from dataclasses import dataclass, field

from app.llm.prompts import REFUSAL_STEM, build_qa_user_prompt, build_system_prompt
from app.llm.providers.base import ChatMessage
from app.llm.router import generate as llm_generate
from app.retrieval.retriever import RetrievedChunk

# Two-stage parse: find each bracketed group, then find every "Doc N[, p.X[-Y]]" segment
# inside it - the LLM sometimes combines several citations into one bracket, e.g.
# "[Doc 1, p.1; Doc 5, p.16]", which a single non-nested regex can't capture correctly.
# The page group tolerates a range ("p.19-20", from multi-page context blocks) by citing
# the range's first page.
BRACKET_RE = re.compile(r"\[([^\]]*)\]")
CITATION_SEGMENT_RE = re.compile(r"Doc\s*(\d+)(?:\s*,\s*p\.?\s*(\d+)(?:\s*-\s*\d+)?)?", re.IGNORECASE)


@dataclass
class Citation:
    doc_index: int
    chunk_id: str
    document_id: str
    arxiv_id: str | None
    page: int | None
    marker_text: str


@dataclass
class AnswerResult:
    text: str
    citations: list[Citation] = field(default_factory=list)
    is_refusal: bool = False
    provider: str = ""
    model: str = ""
    token_usage: dict = field(default_factory=dict)
    latency_ms: int = 0
    retrieved_chunk_ids: list[str] = field(default_factory=list)


def parse_citations(answer_text: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    """Resolves [Doc N, p.X] markers back to real chunks via the ordered list actually sent
    this turn. A doc_index outside that range is a hallucinated citation and is dropped -
    the eval harness's citation-precision metric checks for exactly this via
    `retrieved_chunk_ids` (see project plan's Stage 1 deterministic check)."""
    citations = []
    for bracket in BRACKET_RE.finditer(answer_text):
        for seg in CITATION_SEGMENT_RE.finditer(bracket.group(1)):
            doc_index = int(seg.group(1))
            if not (1 <= doc_index <= len(chunks)):
                continue
            chunk = chunks[doc_index - 1]
            page_str = seg.group(2)
            citations.append(
                Citation(
                    doc_index=doc_index,
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    arxiv_id=chunk.arxiv_id,
                    page=int(page_str) if page_str else chunk.page_start,
                    marker_text=f"[{seg.group(0)}]",
                )
            )
    return citations


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    answer_format: str = "concise",
) -> AnswerResult:
    if not chunks:
        return AnswerResult(text=REFUSAL_STEM, is_refusal=True)

    system_prompt = build_system_prompt(answer_format)
    user_prompt = build_qa_user_prompt(question, chunks)
    messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=user_prompt)]

    t0 = time.perf_counter()
    result = llm_generate(messages, temperature=0.2)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    is_refusal = REFUSAL_STEM.strip().lower() in result.text.strip().lower()
    citations = [] if is_refusal else parse_citations(result.text, chunks)

    return AnswerResult(
        text=result.text,
        citations=citations,
        is_refusal=is_refusal,
        provider=result.provider,
        model=result.model,
        token_usage=result.token_usage,
        latency_ms=latency_ms,
        retrieved_chunk_ids=[c.chunk_id for c in chunks],
    )
