from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM providers
    openai_api_key: str = ""
    gemini_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    gemini_chat_model: str = "gemini-2.5-flash"

    # Database
    database_url: str = "postgresql+psycopg2://researchvault:researchvault@localhost:5432/researchvault"

    # Storage
    data_dir: Path = REPO_ROOT / "data"
    pdf_dir: Path = REPO_ROOT / "data" / "pdfs"
    chroma_dir: Path = REPO_ROOT / "data" / "chroma"

    # arXiv ingestion
    arxiv_user_agent: str = "ResearchVault/0.1 (personal research assistant)"
    arxiv_rate_limit_seconds: float = 3.0

    # App
    env: str = "development"
    log_level: str = "INFO"
    owner_email: str = "alientimesg@gmail.com"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.pdf_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return settings
