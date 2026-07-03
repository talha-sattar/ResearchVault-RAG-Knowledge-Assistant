import re
from dataclasses import dataclass, field
from functools import lru_cache

import tiktoken

from app.config import get_settings
from app.db.enums import ChunkLevel, ChunkingStrategy, SectionType
from app.ingestion.pdf_parser import ParsedDocument

PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")


@lru_cache
def get_encoder() -> tiktoken.Encoding:
    settings = get_settings()
    try:
        return tiktoken.encoding_for_model(settings.openai_embedding_model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(get_encoder().encode(text))


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in PARAGRAPH_SPLIT_RE.split(text) if p.strip()]


def split_paragraphs_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Paragraph text plus its (char_start, char_end) span within `text`."""
    result: list[tuple[str, int, int]] = []
    last_end = 0
    boundaries = [m.span() for m in PARAGRAPH_SPLIT_RE.finditer(text)]
    boundaries.append((len(text), len(text)))
    for sep_start, sep_end in boundaries:
        raw = text[last_end:sep_start]
        stripped = raw.strip()
        if stripped:
            lstripped_len = len(raw) - len(raw.lstrip())
            start = last_end + lstripped_len
            result.append((stripped, start, start + len(stripped)))
        last_end = sep_end
    return result


@dataclass
class Chunk:
    content: str
    section_type: SectionType
    chunk_level: ChunkLevel
    chunk_index: int
    page_start: int
    page_end: int
    char_start: int
    char_end: int
    token_count: int
    parent_index: int | None = None  # index into the same result list (parent_child strategy only)


@dataclass
class _SectionSpan:
    section: object  # ParsedSection
    flat_start: int
    flat_end: int


@dataclass
class FlatDoc:
    text: str
    spans: list[_SectionSpan] = field(default_factory=list)

    def locate(self, char_pos: int):
        """Flat char position -> (ParsedSection, offset local to that section's own text)."""
        for span in self.spans:
            if span.flat_start <= char_pos < span.flat_end:
                return span.section, char_pos - span.flat_start
        if self.spans:
            last = self.spans[-1]
            return last.section, len(last.section.text)
        raise ValueError("Empty document: no sections to locate within")

    def section_at(self, char_pos: int):
        return self.locate(char_pos)[0]

    def page_range_at(self, char_start: int, char_end: int) -> tuple[int, int]:
        start_section, start_local = self.locate(char_start)
        end_section, end_local = self.locate(max(char_start, char_end - 1))
        return start_section.page_at(start_local), end_section.page_at(end_local)


def build_flat_doc(parsed: ParsedDocument) -> FlatDoc:
    """Concatenate section texts, tracking char-offset -> section for span lookups."""
    parts: list[str] = []
    spans: list[_SectionSpan] = []
    cursor = 0
    for section in parsed.sections:
        start = cursor
        parts.append(section.text)
        cursor += len(section.text)
        spans.append(_SectionSpan(section=section, flat_start=start, flat_end=cursor))
        parts.append("\n\n")
        cursor += 2
    return FlatDoc(text="".join(parts), spans=spans)


class Chunker:
    strategy: ChunkingStrategy

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        raise NotImplementedError
