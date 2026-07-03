from app.db.enums import ChunkingStrategy, ChunkLevel, SectionType
from app.ingestion.chunkers import CHUNKERS
from app.ingestion.chunkers.fixed_size import WINDOW_TOKENS
from app.ingestion.chunkers.parent_child import CHILD_WINDOW_TOKENS, MAX_PARENT_TOKENS
from app.ingestion.chunkers.section_aware import MAX_SECTION_TOKENS
from app.ingestion.pdf_parser import ParsedDocument, ParsedSection


def _make_section(section_type, page_start, page_end, num_words, order_index) -> ParsedSection:
    # One "paragraph" per ~40 words so paragraph-aware splitting has something to work with.
    words = [f"w{i}" for i in range(num_words)]
    paragraphs = [" ".join(words[i : i + 40]) for i in range(0, len(words), 40)]
    text = "\n\n".join(paragraphs)
    section = ParsedSection(
        section_type=section_type,
        heading_text=section_type.value,
        text=text,
        page_start=page_start,
        page_end=page_end,
        order_index=order_index,
    )
    # Roughly spread page breaks evenly across the section's text for a more realistic test.
    num_pages = page_end - page_start + 1
    for i, page_num in enumerate(range(page_start, page_end + 1)):
        offset = (len(text) * i) // num_pages
        section.page_breaks.append((page_num, offset))
    return section


def _sample_doc() -> ParsedDocument:
    return ParsedDocument(
        sections=[
            _make_section(SectionType.ABSTRACT, 1, 1, 80, 0),
            _make_section(SectionType.INTRODUCTION, 1, 2, 400, 1),
            _make_section(SectionType.METHODOLOGY, 2, 4, 1200, 2),
            _make_section(SectionType.RESULTS, 4, 5, 600, 3),
            _make_section(SectionType.REFERENCES, 5, 6, 300, 4),
        ],
        num_pages=6,
    )


def test_fixed_size_chunks_respect_token_budget():
    chunks = CHUNKERS[ChunkingStrategy.FIXED_SIZE].chunk(_sample_doc())
    assert chunks
    for c in chunks:
        assert c.token_count <= WINDOW_TOKENS
        assert c.chunk_level == ChunkLevel.LEAF
        assert 1 <= c.page_start <= 6
        assert 1 <= c.page_end <= 6
        assert c.page_start <= c.page_end


def test_section_aware_preserves_section_boundaries():
    chunks = CHUNKERS[ChunkingStrategy.SECTION_AWARE].chunk(_sample_doc())
    assert chunks
    # No chunk should mix content from two different section_types by construction,
    # and no single leaf chunk should wildly exceed the section token budget.
    for c in chunks:
        assert c.token_count <= MAX_SECTION_TOKENS * 1.5  # paragraphs can push slightly over
        assert c.chunk_level == ChunkLevel.LEAF

    section_types_seen = {c.section_type for c in chunks}
    assert section_types_seen == {
        SectionType.ABSTRACT,
        SectionType.INTRODUCTION,
        SectionType.METHODOLOGY,
        SectionType.RESULTS,
        SectionType.REFERENCES,
    }


def test_parent_child_links_are_internally_consistent():
    chunks = CHUNKERS[ChunkingStrategy.PARENT_CHILD].chunk(_sample_doc())
    parents = [c for c in chunks if c.chunk_level == ChunkLevel.PARENT]
    children = [c for c in chunks if c.chunk_level == ChunkLevel.CHILD]
    assert parents and children

    for child in children:
        assert child.parent_index is not None
        parent = chunks[child.parent_index]
        assert parent.chunk_level == ChunkLevel.PARENT
        assert child.section_type == parent.section_type
        assert child.token_count <= CHILD_WINDOW_TOKENS

    for parent in parents:
        assert parent.token_count <= MAX_PARENT_TOKENS * 1.5


def test_paragraph_chunker_never_splits_mid_paragraph():
    doc = _sample_doc()
    chunks = CHUNKERS[ChunkingStrategy.PARAGRAPH].chunk(doc)
    assert chunks
    flat_paragraph_texts = set()
    for section in doc.sections:
        for p in section.text.split("\n\n"):
            if p.strip():
                flat_paragraph_texts.add(p.strip())

    for c in chunks:
        for p in c.content.split("\n\n"):
            assert p.strip() in flat_paragraph_texts
