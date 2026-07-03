"""Thin client for the public arXiv API (export.arxiv.org/api/query).

Uses the free Atom-feed API rather than the S3 bulk buckets: for a targeted
500-2000 paper corpus across a handful of categories, paging this API and
downloading PDFs directly is simpler and free, versus paying for/parsing
requester-pays S3 tarballs of the entire archive. See the project plan for
the full rationale.
"""

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime

import feedparser
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
_ARXIV_ID_VERSION_RE = re.compile(r"^(?P<id>.+?)(v(?P<version>\d+))?$")


@dataclass
class ArxivPaper:
    arxiv_id: str  # without version suffix, e.g. "2301.12345"
    version: int | None
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    primary_category: str | None
    published_at: datetime | None
    pdf_url: str
    abs_url: str


class ArxivRateLimiter:
    """Simple courtesy rate limiter shared across API + PDF-download requests."""

    def __init__(self, min_interval_seconds: float):
        self.min_interval_seconds = min_interval_seconds
        self._last_request_at: float = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()


_default_limiter: ArxivRateLimiter | None = None


def get_default_limiter() -> ArxivRateLimiter:
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = ArxivRateLimiter(get_settings().arxiv_rate_limit_seconds)
    return _default_limiter


def _parse_arxiv_id(entry_id_url: str) -> tuple[str, int | None]:
    """"http://arxiv.org/abs/2301.12345v2" -> ("2301.12345", 2)"""
    raw_id = entry_id_url.rsplit("/abs/", 1)[-1]
    match = _ARXIV_ID_VERSION_RE.match(raw_id)
    if not match:
        return raw_id, None
    version = match.group("version")
    return match.group("id"), int(version) if version else None


def _entry_to_paper(entry) -> ArxivPaper:
    arxiv_id, version = _parse_arxiv_id(entry.id)

    authors = [a.get("name", "").strip() for a in getattr(entry, "authors", [])]
    authors = [a for a in authors if a]

    categories = sorted({tag.get("term") for tag in getattr(entry, "tags", []) if tag.get("term")})
    primary_category = getattr(entry, "arxiv_primary_category", {}).get("term")

    pdf_url = None
    for link in getattr(entry, "links", []):
        if link.get("type") == "application/pdf":
            pdf_url = link.get("href")
            break
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    published_at = None
    if getattr(entry, "published_parsed", None):
        published_at = datetime(*entry.published_parsed[:6])

    return ArxivPaper(
        arxiv_id=arxiv_id,
        version=version,
        title=" ".join(entry.title.split()),
        abstract=" ".join(entry.summary.split()),
        authors=authors,
        categories=categories,
        primary_category=primary_category,
        published_at=published_at,
        pdf_url=pdf_url,
        abs_url=f"https://arxiv.org/abs/{arxiv_id}",
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPError,)),
)
def _fetch_page(client: httpx.Client, params: dict) -> feedparser.FeedParserDict:
    response = client.get(ARXIV_API_URL, params=params)
    response.raise_for_status()
    feed = feedparser.parse(response.text)
    if feed.bozo and not feed.entries:
        raise httpx.HTTPError(f"Failed to parse arXiv Atom feed: {feed.bozo_exception}")
    return feed


def search_category(
    category: str,
    max_results: int,
    *,
    start: int = 0,
    page_size: int = 100,
    limiter: ArxivRateLimiter | None = None,
) -> list[ArxivPaper]:
    """Page through the arXiv API for a given category (e.g. 'cs.AI')."""
    settings = get_settings()
    limiter = limiter or get_default_limiter()
    papers: list[ArxivPaper] = []

    with httpx.Client(
        headers={"User-Agent": settings.arxiv_user_agent}, timeout=30.0, follow_redirects=True
    ) as client:
        fetched = 0
        while fetched < max_results:
            batch = min(page_size, max_results - fetched)
            params = {
                "search_query": f"cat:{category}",
                "start": start + fetched,
                "max_results": batch,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            limiter.wait()
            feed = _fetch_page(client, params)
            if not feed.entries:
                logger.info("arXiv category %s: no more results after %d", category, fetched)
                break
            for entry in feed.entries:
                papers.append(_entry_to_paper(entry))
            fetched += len(feed.entries)
            logger.info("arXiv category %s: fetched %d/%d", category, fetched, max_results)
            if len(feed.entries) < batch:
                break  # exhausted this category

    return papers
