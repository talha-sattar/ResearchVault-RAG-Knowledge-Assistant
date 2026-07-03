import uuid

from sqlalchemy.orm import Session

from app.llm.generation import AnswerResult, generate_answer
from app.llm.prompts import compare_task
from app.retrieval.representative import representative_chunks_for_documents


def compare_documents(db: Session, document_ids: list[uuid.UUID], aspect: str | None = None) -> AnswerResult:
    chunks = representative_chunks_for_documents(db, document_ids, per_section=1, max_per_doc=6)
    return generate_answer(compare_task(aspect), chunks, answer_format="detailed")
