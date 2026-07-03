from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import get_settings

PRODUCTION_COLLECTION_NAME = "researchvault_chunks"


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.PersistentClient(path=str(settings.chroma_dir))


def get_production_collection() -> Collection:
    return get_chroma_client().get_or_create_collection(
        PRODUCTION_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
