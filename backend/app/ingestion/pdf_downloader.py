import logging
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.ingestion.arxiv_client import ArxivRateLimiter, get_default_limiter

logger = logging.getLogger(__name__)


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPError,)),
)
def _stream_download(client: httpx.Client, url: str, dest: Path) -> None:
    with client.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        tmp_path = dest.with_suffix(".part")
        with open(tmp_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=1 << 16):
                f.write(chunk)
        tmp_path.replace(dest)


def download_pdf(
    arxiv_id: str,
    pdf_url: str,
    *,
    limiter: ArxivRateLimiter | None = None,
) -> Path | None:
    """Download a paper's PDF into PDF_DIR, skipping if already present. Returns local path or None on failure."""
    settings = get_settings()
    limiter = limiter or get_default_limiter()
    dest = settings.pdf_dir / f"{arxiv_id}.pdf"

    if dest.exists() and dest.stat().st_size > 0:
        return dest

    limiter.wait()
    try:
        with httpx.Client(headers={"User-Agent": settings.arxiv_user_agent}, timeout=60.0) as client:
            _stream_download(client, pdf_url, dest)
    except httpx.HTTPError as exc:
        logger.warning("Failed to download PDF for %s: %s", arxiv_id, exc)
        return None

    return dest
