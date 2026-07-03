from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import NotFoundError
from app.core.logging import setup_logging
from app.db.base import SessionLocal
from app.routers import chat, collections, compare, health, history, notes, papers, preferences, search
from app.services.bootstrap import ensure_default_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    db = SessionLocal()
    try:
        ensure_default_user(db)
    finally:
        db.close()
    yield


app = FastAPI(title="ResearchVault API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(search.router)
app.include_router(papers.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(collections.router)
app.include_router(notes.router)
app.include_router(preferences.router)
app.include_router(history.router)
