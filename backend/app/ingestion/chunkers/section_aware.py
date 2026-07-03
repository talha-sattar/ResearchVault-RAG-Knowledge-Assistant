from app.db.enums import ChunkingStrategy, ChunkLevel
from app.ingestion.chunkers.base import Chunk, Chunker, count_tokens, split_paragraphs_with_offsets
from app.ingestion.pdf_parser import ParsedDocument, ParsedSection

MAX_SECTION_TOKENS = 500


class SectionAwareChunker(Chunker):
    """One chunk per detected section; long sections are split at paragraph boundaries
    (not mid-sentence) into multiple chunks that keep the same section_type."""

    strategy = ChunkingStrategy.SECTION_AWARE

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0
        for section in parsed.sections:
            if not section.text.strip():
                continue
            for content, local_start, local_end, token_count in split_section(section, MAX_SECTION_TOKENS):
                chunks.append(
                    Chunk(
                        content=content,
                        section_type=section.section_type,
                        chunk_level=ChunkLevel.LEAF,
                        chunk_index=chunk_index,
                        page_start=section.page_at(local_start),
                        page_end=section.page_at(max(local_start, local_end - 1)),
                        char_start=local_start,
                        char_end=local_end,
                        token_count=token_count,
                    )
                )
                chunk_index += 1
        return chunks


def split_section(section: ParsedSection, max_tokens: int = MAX_SECTION_TOKENS) -> list[tuple[str, int, int, int]]:
    total_tokens = count_tokens(section.text)
    if total_tokens <= max_tokens:
        return [(section.text, 0, len(section.text), total_tokens)]

    paragraphs = split_paragraphs_with_offsets(section.text)
    if not paragraphs:
        return [(section.text, 0, len(section.text), total_tokens)]

    groups: list[tuple[str, int, int, int]] = []
    group_parts: list[str] = []
    group_start = paragraphs[0][1]
    group_end = paragraphs[0][1]
    group_tokens = 0

    for text, start, end in paragraphs:
        tokens = count_tokens(text)
        if group_parts and group_tokens + tokens > max_tokens:
            groups.append(("\n\n".join(group_parts), group_start, group_end, group_tokens))
            group_parts = []
            group_tokens = 0
            group_start = start
        if not group_parts:
            group_start = start
        group_parts.append(text)
        group_end = end
        group_tokens += tokens

    if group_parts:
        groups.append(("\n\n".join(group_parts), group_start, group_end, group_tokens))

    return groups
