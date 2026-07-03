REFUSAL_STEM = "I don't have enough information in your collection to answer this."

ANSWER_FORMAT_INSTRUCTIONS = {
    "concise": "Answer in 2-4 sentences.",
    "detailed": "Answer thoroughly, covering all relevant detail the passages support.",
    "bullet_points": "Answer as a concise bulleted list.",
}

BASE_SYSTEM_PROMPT = """You are ResearchVault, a research assistant that answers strictly using the \
numbered source passages given by the user. Rules:
1. Every factual claim must be followed by a citation in the form [Doc N, p.X] referencing the \
passage(s) it came from.
2. Only cite passage numbers that were actually provided - never invent a document number or page.
3. Answer using whatever relevant information the passages DO contain, even if it's partial or \
doesn't cover every angle of the request - a partial, well-cited answer is always better than a refusal.
4. Only respond with EXACTLY this sentence and nothing else if the passages are wholly unrelated to \
the request (contain no relevant information at all): "{refusal_stem}"
5. {format_instruction}
"""


def build_system_prompt(answer_format: str = "concise") -> str:
    instruction = ANSWER_FORMAT_INSTRUCTIONS.get(answer_format, ANSWER_FORMAT_INSTRUCTIONS["concise"])
    return BASE_SYSTEM_PROMPT.format(refusal_stem=REFUSAL_STEM, format_instruction=instruction)


def format_context_block(index: int, chunk) -> str:
    page = f"p.{chunk.page_start}" if chunk.page_start == chunk.page_end else f"p.{chunk.page_start}-{chunk.page_end}"
    return f"[Doc {index} | arXiv:{chunk.arxiv_id} | {page} | {chunk.section_type}]\n{chunk.content}"


def build_qa_user_prompt(question: str, chunks: list) -> str:
    context = "\n\n".join(format_context_block(i + 1, c) for i, c in enumerate(chunks))
    return f"SOURCE PASSAGES:\n\n{context}\n\nQUESTION: {question}"


def summarize_task() -> str:
    return "Provide a summary of this paper: its motivation, method, and key results."


def extract_task() -> str:
    return (
        "Extract and clearly structure the following from the passages, using these exact headers: "
        "Methodology, Datasets, Models, Results. If a header has no information in the provided "
        "passages, write 'Not specified in the provided passages.' under it."
    )


def compare_task(aspect: str | None = None) -> str:
    base = "Compare the papers represented in the passages below"
    if aspect:
        base += f", focusing specifically on: {aspect}"
    return base + ". Organize your answer by paper, then summarize key similarities and differences."
