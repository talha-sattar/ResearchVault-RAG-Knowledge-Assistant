import enum


class DocumentSource(str, enum.Enum):
    ARXIV = "arxiv"
    WIKIPEDIA = "wikipedia"


class ParseStatus(str, enum.Enum):
    PENDING = "pending"
    PARSED = "parsed"
    LOW_TEXT = "low_text"
    FAILED = "failed"


class ChunkingStrategy(str, enum.Enum):
    FIXED_SIZE = "fixed_size"
    PARAGRAPH = "paragraph"
    SECTION_AWARE = "section_aware"
    PARENT_CHILD = "parent_child"


class ChunkLevel(str, enum.Enum):
    LEAF = "leaf"  # fixed_size / paragraph strategies
    PARENT = "parent"
    CHILD = "child"


class SectionType(str, enum.Enum):
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    RELATED_WORK = "related_work"
    METHODOLOGY = "methodology"
    EXPERIMENTS = "experiments"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    LIMITATIONS = "limitations"
    REFERENCES = "references"
    OTHER = "other"


class ConversationScope(str, enum.Enum):
    SINGLE_PAPER = "single_paper"
    MULTI_PAPER = "multi_paper"
    GENERAL = "general"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AnswerFormat(str, enum.Enum):
    CONCISE = "concise"
    DETAILED = "detailed"
    BULLET_POINTS = "bullet_points"


class SearchType(str, enum.Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class ViewType(str, enum.Enum):
    SEARCH_RESULT_CLICK = "search_result_click"
    DETAIL_OPEN = "detail_open"
    CHAT_REFERENCE = "chat_reference"
    COMPARE = "compare"
