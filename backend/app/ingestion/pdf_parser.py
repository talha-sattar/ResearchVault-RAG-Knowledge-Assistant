"""Heuristic section-aware PDF parsing (no GROBID - see plan for rationale).

Title/authors/abstract/categories come from arXiv API metadata, not the PDF.
This module's only job is to split a paper's body text into sections tagged
with a canonical `section_type`, using pymupdf4llm's font-size-aware markdown
heading detection as the primary signal, with a coarser page-level fallback
(raw span/font analysis) for documents where that under-detects.
"""

import logging
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # pymupdf
import pymupdf4llm

from app.db.enums import ParseStatus, SectionType

logger = logging.getLogger(__name__)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
_PICTURE_TEXT_RE = re.compile(
    r"<!--\s*Start of picture text\s*-->.*?<!--\s*End of picture text\s*-->", re.DOTALL | re.IGNORECASE
)
_HTML_TAG_RE = re.compile(r"</?(?:br|sup|sub)\s*/?>", re.IGNORECASE)
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def _clean_page_text(text: str) -> str:
    """pymupdf4llm emits noisy OCR'd figure/table captions and stray pseudo-HTML tags -
    strip both so embeddings aren't polluted with irrelevant image-caption text."""
    text = _PICTURE_TEXT_RE.sub(" ", text)
    text = _HTML_TAG_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text
MIN_HEADINGS_FOR_PRIMARY_PATH = 3
LOW_TEXT_CHAR_THRESHOLD = 2000
MAX_HEADING_LINE_WORDS = 10
NUMBERED_HEADING_RE = re.compile(r"^[A-Z]?\d*(\.\d+)*\.?\s*[A-Z]")

# Order matters: first matching pattern wins.
_SECTION_KEYWORDS: list[tuple[SectionType, re.Pattern]] = [
    (SectionType.ABSTRACT, re.compile(r"\babstract\b", re.I)),
    (SectionType.REFERENCES, re.compile(r"\b(references|bibliography)\b", re.I)),
    (SectionType.RELATED_WORK, re.compile(r"\b(related\s+work|background)\b", re.I)),
    (SectionType.LIMITATIONS, re.compile(r"\blimitations?\b", re.I)),
    (SectionType.CONCLUSION, re.compile(r"\bconclusions?\b", re.I)),
    (SectionType.DISCUSSION, re.compile(r"\bdiscussion\b", re.I)),
    (SectionType.METHODOLOGY, re.compile(r"\b(method\w*|approach\w*|proposed\s+method)\b", re.I)),
    # RESULTS checked before EXPERIMENTS: "Experimental Results" should land on the more
    # specific signal (results) rather than "experiment\w*" matching "Experimental" first.
    (SectionType.RESULTS, re.compile(r"\b(results?|findings)\b", re.I)),
    (SectionType.EXPERIMENTS, re.compile(r"\b(experiment\w*|evaluation\w*)\b", re.I)),
    (SectionType.INTRODUCTION, re.compile(r"\bintroduction\b", re.I)),
]


def classify_heading(heading_text: str) -> SectionType:
    clean = _strip_markdown(heading_text)
    for section_type, pattern in _SECTION_KEYWORDS:
        if pattern.search(clean):
            return section_type
    return SectionType.OTHER


def _strip_markdown(text: str) -> str:
    text = re.sub(r"[*_`]", "", text).strip()
    text = re.sub(r"^[A-Z]?\d*(\.\d+)*\.?\s+", "", text)  # leading numbering: "3.1 ", "A ", "1 "
    return text.strip()


@dataclass
class ParsedSection:
    section_type: SectionType
    heading_text: str
    text: str
    page_start: int
    page_end: int
    order_index: int
    # [(page_number, char_offset_within_text_where_that_page's_content_begins), ...] in increasing offset order.
    page_breaks: list[tuple[int, int]] = field(default_factory=list)

    def page_at(self, local_offset: int) -> int:
        """Which page a given char offset *within this section's text* falls on."""
        page = self.page_start
        for page_num, offset in self.page_breaks:
            if offset <= local_offset:
                page = page_num
            else:
                break
        return page


@dataclass
class ParsedDocument:
    sections: list[ParsedSection] = field(default_factory=list)
    num_pages: int = 0
    parse_status: ParseStatus = ParseStatus.PENDING
    used_fallback: bool = False

    @property
    def full_text(self) -> str:
        return "\n\n".join(s.text for s in self.sections)


def _dominant_heading_level(pages: list[dict]) -> int | None:
    counts: dict[int, int] = {}
    for page in pages:
        for m in HEADING_RE.finditer(page["text"]):
            level = len(m.group(1))
            counts[level] = counts.get(level, 0) + 1
    for level in sorted(counts):
        if counts[level] >= MIN_HEADINGS_FOR_PRIMARY_PATH:
            return level
    return max(counts, key=counts.get) if counts else None


def _parse_via_markdown_headings(pages: list[dict], top_level: int) -> list[ParsedSection]:
    sections: list[ParsedSection] = []
    current: ParsedSection | None = None
    order_index = 0

    for page_idx, page in enumerate(pages):
        page_num = page_idx + 1
        text = page["text"]
        pos = 0
        for m in HEADING_RE.finditer(text):
            level = len(m.group(1))
            start, end = m.span()
            before = text[pos:start]
            if current is not None and before:
                current.page_breaks.append((page_num, len(current.text)))
                current.text += before
                current.page_end = page_num
            if level == top_level:
                if current is not None:
                    sections.append(current)
                heading_text = m.group(2)
                current = ParsedSection(
                    section_type=classify_heading(heading_text),
                    heading_text=_strip_markdown(heading_text),
                    text="",
                    page_start=page_num,
                    page_end=page_num,
                    order_index=order_index,
                )
                current.page_breaks.append((page_num, 0))
                order_index += 1
            pos = end
        tail = text[pos:]
        if current is not None and tail:
            current.page_breaks.append((page_num, len(current.text)))
            current.text += tail
            current.page_end = page_num
        elif current is None and page_idx == 0:
            # Preamble before the first detected heading (title/author block) - own bucket.
            current = ParsedSection(
                section_type=SectionType.OTHER,
                heading_text="",
                text=tail,
                page_start=page_num,
                page_end=page_num,
                order_index=order_index,
            )
            current.page_breaks.append((page_num, 0))
            order_index += 1

    if current is not None:
        sections.append(current)
    return [s for s in sections if s.text.strip()]


def _span_heading_candidates(doc: fitz.Document) -> dict[int, list[str]]:
    """Coarse fallback: font-size/boldness based heading detection, one bucket of headings per page."""
    sizes = []
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        sizes.append(round(span["size"], 1))
    if not sizes:
        return {}
    body_size = statistics.mode(sizes)

    headings_by_page: dict[int, list[str]] = {}
    for page_idx, page in enumerate(doc):
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                if not text or len(text.split()) > MAX_HEADING_LINE_WORDS:
                    continue
                max_size = max(s["size"] for s in spans)
                is_bold = any("bold" in s.get("font", "").lower() for s in spans)
                looks_like_heading = max_size > body_size * 1.15 or is_bold
                if looks_like_heading and (NUMBERED_HEADING_RE.match(text) or len(text.split()) <= 6):
                    headings_by_page.setdefault(page_idx + 1, []).append(text)
    return headings_by_page


def _parse_via_page_level_fallback(pages: list[dict], doc: fitz.Document) -> list[ParsedSection]:
    """Page-granularity fallback when markdown heading detection finds too few headings."""
    headings_by_page = _span_heading_candidates(doc)
    sections: list[ParsedSection] = []
    current: ParsedSection | None = None
    order_index = 0

    for page_idx, page in enumerate(pages):
        page_num = page_idx + 1
        candidate_headings = headings_by_page.get(page_num, [])
        if candidate_headings and current is not None:
            sections.append(current)
            current = None
        if current is None:
            heading_text = candidate_headings[0] if candidate_headings else ""
            current = ParsedSection(
                section_type=classify_heading(heading_text) if heading_text else SectionType.OTHER,
                heading_text=_strip_markdown(heading_text),
                text=page["text"],
                page_start=page_num,
                page_end=page_num,
                order_index=order_index,
            )
            current.page_breaks.append((page_num, 0))
            order_index += 1
        else:
            current.page_breaks.append((page_num, len(current.text) + 2))  # +2 for the "\n\n" join below
            current.text += "\n\n" + page["text"]
            current.page_end = page_num

    if current is not None:
        sections.append(current)
    return [s for s in sections if s.text.strip()]


def parse_pdf(pdf_path: Path) -> ParsedDocument:
    try:
        pages = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)
    except Exception:
        logger.exception("Failed to parse PDF %s", pdf_path)
        return ParsedDocument(parse_status=ParseStatus.FAILED)

    for page in pages:
        page["text"] = _clean_page_text(page["text"])

    num_pages = len(pages)
    top_level = _dominant_heading_level(pages)
    used_fallback = False

    if top_level is not None:
        sections = _parse_via_markdown_headings(pages, top_level)
    else:
        sections = []

    if len(sections) < MIN_HEADINGS_FOR_PRIMARY_PATH:
        try:
            with fitz.open(str(pdf_path)) as doc:
                fallback_sections = _parse_via_page_level_fallback(pages, doc)
            if len(fallback_sections) > len(sections):
                sections = fallback_sections
                used_fallback = True
        except Exception:
            logger.warning("Span-based fallback parsing failed for %s", pdf_path, exc_info=True)

    total_chars = sum(len(s.text) for s in sections)
    parse_status = ParseStatus.LOW_TEXT if total_chars < LOW_TEXT_CHAR_THRESHOLD else ParseStatus.PARSED

    return ParsedDocument(
        sections=sections,
        num_pages=num_pages,
        parse_status=parse_status,
        used_fallback=used_fallback,
    )
