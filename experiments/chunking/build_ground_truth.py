"""Builds LLM-drafted retrieval ground truth for the chunking experiment.

Samples ~30 already-ingested papers (stratified across categories), asks an
LLM to draft 2-3 questions per paper grounded in its Methodology/Experiments/
Results sections, locates each answer's verbatim excerpt back in the parsed
text to get an authoritative page number (not trusted from the LLM), and
writes experiments/chunking/ground_truth.jsonl.

Usage (run with the backend venv's python from the repo root):
    backend/.venv/Scripts/python.exe experiments/chunking/build_ground_truth.py --sample-size 30
"""

import argparse
import json
import logging
import random
import sys
from pathlib import Path

from openai import OpenAI
from rapidfuzz import fuzz
from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.enums import SectionType  # noqa: E402
from app.db.models import Document  # noqa: E402
from app.ingestion.pdf_parser import ParsedSection, parse_pdf  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).resolve().parent / "ground_truth.jsonl"
TARGET_SECTION_TYPES = {SectionType.METHODOLOGY, SectionType.EXPERIMENTS, SectionType.RESULTS}
QUESTIONS_PER_SECTION = 2
FUZZY_MATCH_THRESHOLD = 80

QUESTION_PROMPT = """You are building a retrieval evaluation set for a research-paper Q&A system.

Below is one section (type: {section_type}) from a paper titled "{title}".

Write {n} distinct, specific questions that this passage - and only this passage - answers well \
(favor concrete details: numbers, dataset names, model names, procedure steps). For each question, \
also copy a VERBATIM excerpt (1-3 sentences, exact substring of the passage below, no paraphrasing, \
no ellipses) that directly contains the answer.

Return ONLY a JSON object: {{"questions": [{{"question": "...", "gold_excerpt": "..."}}, ...]}}

PASSAGE:
\"\"\"
{passage}
\"\"\"
"""


def sample_documents(session, sample_size: int) -> list[Document]:
    docs = session.execute(
        select(Document).where(Document.pdf_local_path.is_not(None))
    ).scalars().all()
    if not docs:
        raise SystemExit("No ingested documents with downloaded PDFs found - run ingestion first.")

    by_category: dict[str, list[Document]] = {}
    for d in docs:
        by_category.setdefault(d.primary_category or "unknown", []).append(d)

    categories = sorted(by_category)
    rng = random.Random(42)
    for docs_in_cat in by_category.values():
        rng.shuffle(docs_in_cat)

    sample: list[Document] = []
    seen_ids = set()
    i = 0
    while len(sample) < sample_size and any(by_category.values()):
        cat = categories[i % len(categories)]
        bucket = by_category[cat]
        if bucket:
            doc = bucket.pop()
            if doc.id not in seen_ids:
                sample.append(doc)
                seen_ids.add(doc.id)
        i += 1
        if i > sample_size * 20:
            break
    return sample


def locate_excerpt(section: ParsedSection, excerpt: str) -> tuple[int, int] | None:
    """Fuzzy-locate `excerpt` inside section.text, return (char_offset, score) of best window."""
    text = section.text
    if not text.strip() or not excerpt.strip():
        return None
    best_score = 0
    best_offset = None
    window = len(excerpt)
    step = max(1, window // 4)
    for start in range(0, max(1, len(text) - window + step), step):
        candidate = text[start : start + window + step]
        score = fuzz.partial_ratio(excerpt, candidate)
        if score > best_score:
            best_score = score
            best_offset = start
    if best_offset is None or best_score < FUZZY_MATCH_THRESHOLD:
        return None
    return best_offset, best_score


def draft_questions_for_section(client: OpenAI, model: str, title: str, section: ParsedSection) -> list[dict]:
    passage = section.text[:6000]
    prompt = QUESTION_PROMPT.format(
        section_type=section.section_type.value, title=title, n=QUESTIONS_PER_SECTION, passage=passage
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message.content)
    except Exception:
        logger.exception("LLM question drafting failed for section %s of %r", section.section_type, title)
        return []
    return data.get("questions", [])


def build_ground_truth(sample_size: int) -> None:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    session = SessionLocal()

    records = []
    try:
        documents = sample_documents(session, sample_size)
        logger.info("Sampled %d documents across categories", len(documents))

        for i, doc in enumerate(documents, start=1):
            pdf_path = Path(doc.pdf_local_path)
            if not pdf_path.exists():
                continue
            parsed = parse_pdf(pdf_path)
            target_sections = [s for s in parsed.sections if s.section_type in TARGET_SECTION_TYPES]
            if not target_sections:
                logger.info("[%d/%d] %s: no methodology/experiments/results sections found, skipping", i, len(documents), doc.arxiv_id)
                continue

            for section in target_sections:
                questions = draft_questions_for_section(client, settings.openai_chat_model, doc.title, section)
                for q in questions:
                    question_text = q.get("question", "").strip()
                    excerpt = q.get("gold_excerpt", "").strip()
                    if not question_text or not excerpt:
                        continue
                    located = locate_excerpt(section, excerpt)
                    if located is None:
                        logger.info("Discarding unlocatable excerpt for %s: %r", doc.arxiv_id, excerpt[:80])
                        continue
                    offset, score = located
                    records.append(
                        {
                            "arxiv_id": doc.arxiv_id,
                            "title": doc.title,
                            "question": question_text,
                            "gold_excerpt": excerpt,
                            "gold_section_type": section.section_type.value,
                            "gold_page": section.page_at(offset),
                            "match_score": score,
                            "verified": False,
                        }
                    )
            logger.info("[%d/%d] %s: %d questions so far", i, len(documents), doc.arxiv_id, len(records))
    finally:
        session.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    logger.info("Wrote %d ground-truth questions to %s", len(records), OUTPUT_PATH)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=30)
    args = parser.parse_args()
    build_ground_truth(args.sample_size)


if __name__ == "__main__":
    main()
