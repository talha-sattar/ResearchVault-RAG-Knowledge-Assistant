from app.db.enums import ChunkingStrategy
from app.ingestion.chunkers.base import Chunk, Chunker
from app.ingestion.chunkers.fixed_size import FixedSizeChunker
from app.ingestion.chunkers.paragraph import ParagraphChunker
from app.ingestion.chunkers.parent_child import ParentChildChunker
from app.ingestion.chunkers.section_aware import SectionAwareChunker

CHUNKERS: dict[ChunkingStrategy, Chunker] = {
    ChunkingStrategy.FIXED_SIZE: FixedSizeChunker(),
    ChunkingStrategy.PARAGRAPH: ParagraphChunker(),
    ChunkingStrategy.SECTION_AWARE: SectionAwareChunker(),
    ChunkingStrategy.PARENT_CHILD: ParentChildChunker(),
}

__all__ = ["Chunk", "Chunker", "CHUNKERS"]
