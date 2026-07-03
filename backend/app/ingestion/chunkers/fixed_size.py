from app.db.enums import ChunkingStrategy, ChunkLevel
from app.ingestion.chunkers.base import Chunk, Chunker, build_flat_doc, get_encoder
from app.ingestion.pdf_parser import ParsedDocument

WINDOW_TOKENS = 350
OVERLAP_TOKENS = 50


class FixedSizeChunker(Chunker):
    """Pure token-count sliding window over the whole document, ignoring paragraph/section
    boundaries. Still tags section_type/page range via whichever section covers the window's
    start (the "nearest preceding heading" rule) - the least precise of the four strategies."""

    strategy = ChunkingStrategy.FIXED_SIZE

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        flat = build_flat_doc(parsed)
        if not flat.text.strip():
            return []

        encoder = get_encoder()
        token_ids = encoder.encode(flat.text)
        stride = WINDOW_TOKENS - OVERLAP_TOKENS
        chunks: list[Chunk] = []
        chunk_index = 0

        start_tok = 0
        while start_tok < len(token_ids):
            end_tok = min(start_tok + WINDOW_TOKENS, len(token_ids))
            char_start = len(encoder.decode(token_ids[:start_tok])) if start_tok else 0
            content = encoder.decode(token_ids[start_tok:end_tok])
            char_end = char_start + len(content)

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
                    token_count=end_tok - start_tok,
                )
            )
            chunk_index += 1
            if end_tok == len(token_ids):
                break
            start_tok += stride

        return chunks
