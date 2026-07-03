"""Runs the chunking-strategy comparison: indexes the sampled corpus 4 ways (one
scratch Chroma collection per strategy) and measures Recall@k / MRR / section-type
accuracy against experiments/chunking/ground_truth.jsonl. Writes results/metrics.csv
and REPORT.md with a recommended production chunking strategy.

Usage:
    backend/.venv/Scripts/python.exe experiments/chunking/run_experiment.py
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path

import chromadb
from openai import OpenAI
from rapidfuzz import fuzz
from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.enums import ChunkLevel, ChunkingStrategy  # noqa: E402
from app.db.models import Document  # noqa: E402
from app.ingestion.chunkers import CHUNKERS  # noqa: E402
from app.ingestion.pdf_parser import parse_pdf  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EXPERIMENT_DIR = Path(__file__).resolve().parent
GROUND_TRUTH_PATH = EXPERIMENT_DIR / "ground_truth.jsonl"
SCRATCH_CHROMA_DIR = EXPERIMENT_DIR / "scratch_chroma"
RESULTS_DIR = EXPERIMENT_DIR / "results"
REPORT_PATH = EXPERIMENT_DIR / "REPORT.md"

K_VALUES = (1, 3, 5)
FUZZY_MATCH_THRESHOLD = 80
EMBED_BATCH_SIZE = 100


def load_ground_truth() -> list[dict]:
    if not GROUND_TRUTH_PATH.exists():
        raise SystemExit(f"{GROUND_TRUTH_PATH} not found - run build_ground_truth.py first.")
    records = []
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_parsed_documents(arxiv_ids: set[str]) -> dict[str, tuple[Document, object]]:
    session = SessionLocal()
    try:
        docs = session.execute(
            select(Document).where(Document.arxiv_id.in_(arxiv_ids))
        ).scalars().all()
    finally:
        session.close()

    parsed_by_id = {}
    for doc in docs:
        if not doc.pdf_local_path or not Path(doc.pdf_local_path).exists():
            continue
        parsed_by_id[doc.arxiv_id] = (doc, parse_pdf(Path(doc.pdf_local_path)))
    return parsed_by_id


def embed_texts(client: OpenAI, model: str, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        response = client.embeddings.create(model=model, input=batch)
        vectors.extend([item.embedding for item in response.data])
    return vectors


def index_strategy(
    client: OpenAI,
    settings,
    chroma_client,
    strategy: ChunkingStrategy,
    parsed_by_id: dict,
):
    """Returns (collection, parent_registry) where parent_registry maps
    {chunk_id: {"content": parent_content}} for effective-context expansion."""
    collection_name = f"chunking_exp_{strategy.value}"
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass
    collection = chroma_client.create_collection(collection_name)

    chunker = CHUNKERS[strategy]
    parent_registry: dict[str, dict] = {}

    ids, texts, metadatas = [], [], []
    for arxiv_id, (doc, parsed) in parsed_by_id.items():
        chunks = chunker.chunk(parsed)
        parents_by_local_index = {i: c for i, c in enumerate(chunks) if c.chunk_level == ChunkLevel.PARENT}

        for i, c in enumerate(chunks):
            if c.chunk_level not in (ChunkLevel.LEAF, ChunkLevel.CHILD):
                continue
            chunk_id = f"{arxiv_id}_{i}"
            ids.append(chunk_id)
            texts.append(c.content)
            metadatas.append(
                {
                    "arxiv_id": arxiv_id,
                    "section_type": c.section_type.value,
                    "chunk_level": c.chunk_level.value,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                }
            )
            if c.chunk_level == ChunkLevel.CHILD and c.parent_index in parents_by_local_index:
                parent_registry[chunk_id] = {"content": parents_by_local_index[c.parent_index].content}

    logger.info("[%s] embedding %d chunks", strategy.value, len(texts))
    embeddings = embed_texts(client, settings.openai_embedding_model, texts)

    for i in range(0, len(ids), EMBED_BATCH_SIZE):
        collection.add(
            ids=ids[i : i + EMBED_BATCH_SIZE],
            embeddings=embeddings[i : i + EMBED_BATCH_SIZE],
            documents=texts[i : i + EMBED_BATCH_SIZE],
            metadatas=metadatas[i : i + EMBED_BATCH_SIZE],
        )

    return collection, parent_registry


def fuzzy_hit(gold_excerpt: str, candidate_text: str) -> bool:
    return fuzz.partial_ratio(gold_excerpt, candidate_text) >= FUZZY_MATCH_THRESHOLD


def evaluate_strategy(
    strategy: ChunkingStrategy,
    collection,
    parent_registry: dict,
    ground_truth: list[dict],
    question_embeddings: list[list[float]],
) -> dict:
    max_k = max(K_VALUES)
    strict_hits = {k: 0 for k in K_VALUES}
    effective_hits = {k: 0 for k in K_VALUES}
    section_hits = {k: 0 for k in K_VALUES}
    reciprocal_ranks = []
    evaluated = 0
    latencies = []

    for record, q_emb in zip(ground_truth, question_embeddings):
        t0 = time.perf_counter()
        result = collection.query(
            query_embeddings=[q_emb],
            n_results=max_k,
            where={"arxiv_id": record["arxiv_id"]},
        )
        latencies.append(time.perf_counter() - t0)

        ids = result["ids"][0] if result["ids"] else []
        docs = result["documents"][0] if result["documents"] else []
        metas = result["metadatas"][0] if result["metadatas"] else []
        if not ids:
            evaluated += 1
            reciprocal_ranks.append(0.0)
            continue

        evaluated += 1
        first_hit_rank = None
        for rank, (chunk_id, text, meta) in enumerate(zip(ids, docs, metas), start=1):
            if fuzzy_hit(record["gold_excerpt"], text) and first_hit_rank is None:
                first_hit_rank = rank
        reciprocal_ranks.append(1.0 / first_hit_rank if first_hit_rank else 0.0)

        for k in K_VALUES:
            top_k_ids = ids[:k]
            top_k_docs = docs[:k]
            top_k_metas = metas[:k]

            if any(fuzzy_hit(record["gold_excerpt"], t) for t in top_k_docs):
                strict_hits[k] += 1

            expanded_texts = list(top_k_docs)
            for cid in top_k_ids:
                parent = parent_registry.get(cid)
                if parent:
                    expanded_texts.append(parent["content"])
            if any(fuzzy_hit(record["gold_excerpt"], t) for t in expanded_texts):
                effective_hits[k] += 1

            if any(m.get("section_type") == record["gold_section_type"] for m in top_k_metas):
                section_hits[k] += 1

    n = max(evaluated, 1)
    return {
        "strategy": strategy.value,
        "n_questions": evaluated,
        **{f"recall_strict@{k}": strict_hits[k] / n for k in K_VALUES},
        **{f"recall_effective@{k}": effective_hits[k] / n for k in K_VALUES},
        **{f"section_type_acc@{k}": section_hits[k] / n for k in K_VALUES},
        "mrr": sum(reciprocal_ranks) / n,
        "avg_query_latency_ms": (sum(latencies) / len(latencies)) * 1000 if latencies else 0.0,
    }


def write_report(metrics: list[dict], ground_truth: list[dict]) -> None:
    verified_count = sum(1 for r in ground_truth if r.get("verified"))
    by_strategy = {m["strategy"]: m for m in metrics}
    winner = max(metrics, key=lambda m: m["recall_effective@5"])

    lines = [
        "# Chunking Strategy Experiment Report",
        "",
        f"Ground truth: {len(ground_truth)} questions "
        f"({verified_count} human-spot-checked / {len(ground_truth) - verified_count} unverified LLM-drafted).",
        "",
        "## Results",
        "",
        "| Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@5 (effective) | Section-type Acc@5 | MRR | Avg query latency (ms) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in metrics:
        lines.append(
            f"| {m['strategy']} | {m['recall_strict@1']:.2f} | {m['recall_strict@3']:.2f} | "
            f"{m['recall_strict@5']:.2f} | {m['recall_effective@5']:.2f} | {m['section_type_acc@5']:.2f} | "
            f"{m['mrr']:.3f} | {m['avg_query_latency_ms']:.1f} |"
        )

    lines += [
        "",
        "## Recommendation",
        "",
        f"**{winner['strategy']}** achieved the highest effective-context Recall@5 "
        f"({winner['recall_effective@5']:.2f}) at retrieving the sections needed to answer "
        "methodology/experiments/results questions, and is recommended as the production "
        "chunking strategy for the full corpus index.",
        "",
        "Notes:",
        "- Recall@k (strict) checks the gold excerpt is found in the retrieved chunk text itself.",
        "- Recall@k (effective) additionally counts a hit if expanding a retrieved child chunk to "
        "its parent section contains the gold excerpt (only differs from strict for parent_child).",
        "- Section-type Acc@k checks whether any of the top-k chunks share the gold section's type, "
        "a looser signal than exact excerpt matching.",
        "- Ground truth questions were LLM-drafted (GPT) from real paper sections with excerpts "
        "verified to actually appear in the source text (fuzzy match), then a sample was spot-checked "
        "by a human reviewer rather than exhaustively hand-verified - see Known Limitations in the "
        "project plan.",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %s", REPORT_PATH)


def main():
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    chroma_client = chromadb.PersistentClient(path=str(SCRATCH_CHROMA_DIR))

    ground_truth = load_ground_truth()
    arxiv_ids = {r["arxiv_id"] for r in ground_truth}
    logger.info("Loaded %d ground-truth questions across %d papers", len(ground_truth), len(arxiv_ids))

    parsed_by_id = load_parsed_documents(arxiv_ids)
    logger.info("Parsed %d/%d referenced papers", len(parsed_by_id), len(arxiv_ids))
    ground_truth = [r for r in ground_truth if r["arxiv_id"] in parsed_by_id]

    logger.info("Embedding %d ground-truth questions", len(ground_truth))
    question_embeddings = embed_texts(
        client, settings.openai_embedding_model, [r["question"] for r in ground_truth]
    )

    all_metrics = []
    for strategy in ChunkingStrategy:
        collection, parent_registry = index_strategy(client, settings, chroma_client, strategy, parsed_by_id)
        metrics = evaluate_strategy(strategy, collection, parent_registry, ground_truth, question_embeddings)
        logger.info("[%s] %s", strategy.value, metrics)
        all_metrics.append(metrics)

    RESULTS_DIR.mkdir(exist_ok=True)
    csv_path = RESULTS_DIR / "metrics.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_metrics[0].keys()))
        writer.writeheader()
        writer.writerows(all_metrics)
    logger.info("Wrote %s", csv_path)

    write_report(all_metrics, ground_truth)


if __name__ == "__main__":
    main()
