from app.db.enums import ChunkingStrategy, ChunkLevel
from app.ingestion.chunkers.base import Chunk, Chunker, get_encoder
from app.ingestion.chunkers.section_aware import split_section
from app.ingestion.pdf_parser import ParsedDocument

MAX_PARENT_TOKENS = 1800
CHILD_WINDOW_TOKENS = 350
CHILD_OVERLAP_TOKENS = 50


class ParentChildChunker(Chunker):
    """Parents = section text (split at paragraph boundaries if >MAX_PARENT_TOKENS), each
    keeping the section's section_type. Children = overlapping token windows carved from each
    parent, inheriting section_type and only the page range their own text spans. Children are
    what gets embedded/searched; generation can expand a retrieved child back to its parent."""

    strategy = ChunkingStrategy.PARENT_CHILD

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []

        for section in parsed.sections:
            if not section.text.strip():
                continue
            for content, local_start, local_end, token_count in split_section(section, MAX_PARENT_TOKENS):
                parent_index = len(chunks)
                chunks.append(
                    Chunk(
                        content=content,
                        section_type=section.section_type,
                        chunk_level=ChunkLevel.PARENT,
                        chunk_index=parent_index,
                        page_start=section.page_at(local_start),
                        page_end=section.page_at(max(local_start, local_end - 1)),
                        char_start=local_start,
                        char_end=local_end,
                        token_count=token_count,
                    )
                )
                for child_content, child_local_start, child_local_end, child_tokens in _sliding_windows(content):
                    abs_start = local_start + child_local_start
                    abs_end = local_start + child_local_end
                    chunks.append(
                        Chunk(
                            content=child_content,
                            section_type=section.section_type,
                            chunk_level=ChunkLevel.CHILD,
                            chunk_index=len(chunks),
                            page_start=section.page_at(abs_start),
                            page_end=section.page_at(max(abs_start, abs_end - 1)),
                            char_start=abs_start,
                            char_end=abs_end,
                            token_count=child_tokens,
                            parent_index=parent_index,
                        )
                    )

        return chunks


def _sliding_windows(text: str) -> list[tuple[str, int, int, int]]:
    encoder = get_encoder()
    token_ids = encoder.encode(text)
    if len(token_ids) <= CHILD_WINDOW_TOKENS:
        return [(text, 0, len(text), len(token_ids))]

    stride = CHILD_WINDOW_TOKENS - CHILD_OVERLAP_TOKENS
    windows: list[tuple[str, int, int, int]] = []
    start_tok = 0
    while start_tok < len(token_ids):
        end_tok = min(start_tok + CHILD_WINDOW_TOKENS, len(token_ids))
        char_start = len(encoder.decode(token_ids[:start_tok])) if start_tok else 0
        content = encoder.decode(token_ids[start_tok:end_tok])
        char_end = char_start + len(content)
        windows.append((content, char_start, char_end, end_tok - start_tok))
        if end_tok == len(token_ids):
            break
        start_tok += stride
    return windows
