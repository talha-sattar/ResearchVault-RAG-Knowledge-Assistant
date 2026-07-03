from app.db.enums import ChunkingStrategy, ChunkLevel
from app.ingestion.chunkers.base import (
    Chunk,
    Chunker,
    build_flat_doc,
    count_tokens,
    split_paragraphs_with_offsets,
)
from app.ingestion.pdf_parser import ParsedDocument

TARGET_TOKENS = 350


class ParagraphChunker(Chunker):
    """Greedily groups consecutive paragraphs up to a target token budget. Never splits
    mid-paragraph (a single very long paragraph is kept whole, exceeding the target)."""

    strategy = ChunkingStrategy.PARAGRAPH

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        flat = build_flat_doc(parsed)
        if not flat.text.strip():
            return []

        paragraphs = split_paragraphs_with_offsets(flat.text)
        chunks: list[Chunk] = []
        chunk_index = 0

        group: list[tuple[str, int, int]] = []
        group_tokens = 0

        def flush():
            nonlocal chunk_index, group, group_tokens
            if not group:
                return
            content = "\n\n".join(p[0] for p in group)
            char_start, char_end = group[0][1], group[-1][2]
            page_start, page_end = flat.page_range_at(char_start, char_end)
            section = flat.section_at(char_start)
            chunks.append(
                Chunk(
                    content=content,
                    section_type=section.section_type,
                    chunk_level=ChunkLevel.LEAF,
                    chunk_index=chunk_index,
                    page_start=page_start,
                    page_end=page_end,
                    char_start=char_start,
                    char_end=char_end,
                    token_count=group_tokens,
                )
            )
            chunk_index += 1
            group = []
            group_tokens = 0

        for text, start, end in paragraphs:
            tokens = count_tokens(text)
            if group and group_tokens + tokens > TARGET_TOKENS:
                flush()
            group.append((text, start, end))
            group_tokens += tokens
        flush()

        return chunks
