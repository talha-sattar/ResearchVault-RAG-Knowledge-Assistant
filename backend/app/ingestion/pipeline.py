"""CLI entrypoint for the metadata + PDF ingestion phase.

Usage:
    python -m app.ingestion.pipeline --categories cs.AI,cs.CV,cs.LG,stat.ML --max-per-category 20

Searches each category via the arXiv API, dedupes papers cross-listed in
multiple categories, writes Document/Author rows to Postgres, and downloads
each paper's PDF to PDF_DIR. Safe to re-run: existing documents/PDFs are
skipped or merged, not duplicated.
"""

import argparse
import logging

from app.config import get_settings
from app.core.logging import setup_logging
from app.db.base import SessionLocal
from app.ingestion.arxiv_client import ArxivPaper, search_category
from app.ingestion.metadata_writer import upsert_paper
from app.ingestion.pdf_downloader import download_pdf

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = ["cs.AI", "cs.CV", "cs.LG", "stat.ML"]


def collect_papers(categories: list[str], max_per_category: int) -> dict[str, ArxivPaper]:
    """Search all categories and merge cross-listed papers into one record per arxiv_id."""
    by_id: dict[str, ArxivPaper] = {}
    for category in categories:
        for paper in search_category(category, max_per_category):
            existing = by_id.get(paper.arxiv_id)
            if existing is None:
                by_id[paper.arxiv_id] = paper
            else:
                existing.categories = sorted(set(existing.categories) | set(paper.categories))
    return by_id


def run(categories: list[str], max_per_category: int, skip_download: bool) -> None:
    settings = get_settings()
    logger.info("Searching arXiv categories=%s max_per_category=%d", categories, max_per_category)
    papers_by_id = collect_papers(categories, max_per_category)
    logger.info("Collected %d unique papers across %d categories", len(papers_by_id), len(categories))

    db = SessionLocal()
    written = 0
    downloaded = 0
    failed_downloads = 0
    try:
        for i, paper in enumerate(papers_by_id.values(), start=1):
            document = upsert_paper(db, paper)
            db.commit()
            written += 1

            if not skip_download:
                local_path = download_pdf(paper.arxiv_id, paper.pdf_url)
                if local_path is not None:
                    document.pdf_local_path = str(local_path)
                    db.commit()
                    downloaded += 1
                else:
                    failed_downloads += 1

            if i % 25 == 0:
                logger.info("Progress: %d/%d papers processed", i, len(papers_by_id))
    finally:
        db.close()

    logger.info(
        "Ingestion complete: %d documents written, %d PDFs downloaded, %d download failures. PDFs in %s",
        written,
        downloaded,
        failed_downloads,
        settings.pdf_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest arXiv paper metadata + PDFs into ResearchVault.")
    parser.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="Comma-separated arXiv category codes, e.g. cs.AI,cs.CV,cs.LG,stat.ML",
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=20,
        help="Max papers to fetch per category (before cross-category dedup)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Only write metadata, skip PDF download",
    )
    args = parser.parse_args()

    setup_logging()
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    run(categories, args.max_per_category, args.skip_download)


if __name__ == "__main__":
    main()
