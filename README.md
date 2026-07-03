# ResearchVault — Personal Research Knowledge Assistant

A personal RAG (Retrieval-Augmented Generation) assistant over a curated arXiv research
collection. It searches, summarizes, compares, and answers questions across papers — with
page-level citations back to the source PDF — and learns your preferences, collections, and
reading history along the way.

Built around 500+ papers from `cs.AI`, `cs.CV`, `cs.LG`, and `stat.ML`, ingested directly from
the public arXiv API.

## Features

1. **Semantic search** over indexed papers (hybrid dense + keyword retrieval, cross-encoder reranked)
2. **Multi-paper Q&A** — ask a question and get an answer synthesized across several papers, with citations
3. **Summarize** any indexed paper on demand
4. **Compare** two or more papers side by side
5. **Extract** methodology, datasets, models, and results from a paper into a structured answer
6. **Collections** — save papers into named personal collections
7. **Notes** — attach personal notes to any paper, optionally pinned to a page
8. **Preferences** — favorite topics and a preferred answer style (concise / detailed / bullet points)
9. **Recommendations** — related-paper suggestions via embedding-centroid similarity
10. **Page-level citations** — every generated claim is traceable to `[Doc N, p.X]` in a real source PDF

## Architecture

```
arXiv API (metadata + PDFs)
        │
        ▼
Ingestion  (app/ingestion/pipeline.py)
        │
        ▼
PDF parsing — heuristic section detection (pymupdf4llm + font/heading heuristics)
        │
        ▼
Section-aware chunking  →  4 strategies compared experimentally, see below
        │
        ▼
Embeddings (OpenAI text-embedding-3-small)
        │
        ▼
Vector DB (Chroma, embedded/persistent)  +  Postgres (metadata, full text, FTS)
        │
        ▼
Hybrid retrieval — dense (Chroma) + sparse (Postgres full-text) → Reciprocal Rank Fusion
        │
        ▼
Cross-encoder reranking (sentence-transformers ms-marco-MiniLM-L-6-v2)
        │
        ▼
LLM answer generation (OpenAI primary, Gemini fallback) with citation parsing
        │
        ▼
FastAPI backend  ⇄  React (Vite + TS + Tailwind) frontend
```

### Why these choices

- **arXiv public API, not S3 bulk data** — for a targeted few-thousand-paper corpus across four
  categories, paging the free Atom API and downloading PDFs directly is simpler and free, versus
  paying for and filtering requester-pays S3 tarballs of the entire archive.
- **Heuristic PDF parsing, not GROBID** — title/authors/abstract/categories come from arXiv's
  already-structured metadata, so the PDF parser only needs to locate body-section boundaries. A
  5th Docker service (GROBID) whose main value is bibliography parsing wasn't worth it for that
  narrower problem.
- **Chroma embedded, not a separate vector server** — one less moving part for a project this size;
  still fully Docker-volume-persisted.
- **Embeddings never fall back across providers** — OpenAI and Gemini embeddings live in
  incompatible vector spaces, so silently switching mid-flight would corrupt nearest-neighbor
  search. Only LLM *generation* has a Gemini fallback (safe, since it's just text in/text out).

## The chunking experiment

Per the project brief, four chunking strategies were implemented and compared head-to-head:
fixed-size, paragraph, section-aware, and parent-child. Each was indexed into its own scratch
Chroma collection and evaluated against ~150 LLM-drafted, excerpt-verified questions grounded in
real papers' methodology/experiments/results sections.

| Strategy | Recall@1 | Recall@5 | Recall@5 (effective) | Section-type Acc@5 | MRR |
|---|---|---|---|---|---|
| fixed_size | 0.41 | 0.79 | 0.79 | 0.86 | 0.564 |
| paragraph | 0.48 | 0.77 | 0.77 | 0.89 | 0.600 |
| section_aware | 0.53 | 0.83 | 0.83 | 0.97 | 0.652 |
| **parent_child** | **0.54** | 0.79 | **0.90** | 0.96 | 0.640 |

**parent_child** won on effective-context Recall@5 and is the production chunking strategy. Full
methodology, ground-truth construction, and metric definitions are in
[`experiments/chunking/REPORT.md`](experiments/chunking/REPORT.md).

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Python 3.10 |
| Relational DB | PostgreSQL (full-text search via `tsvector`/GIN, not a separate BM25 index) |
| Vector DB | Chroma (embedded, persistent) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Generation | OpenAI `gpt-4o-mini` primary, Gemini `gemini-2.5-flash` fallback |
| Reranking | `sentence-transformers` cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, React Query, React Router |
| Infra | Docker Compose (Postgres; app services documented, see Status) |

## Repository layout

```
backend/app/
  main.py                 FastAPI app + router registration
  config.py                Settings (pydantic-settings, reads .env)
  db/                     SQLAlchemy models, enums, Alembic migrations
  ingestion/
    arxiv_client.py        arXiv Atom API client (rate-limited)
    pdf_downloader.py
    pdf_parser.py           Section-aware heuristic PDF parsing
    chunkers/               fixed_size / paragraph / section_aware / parent_child
    embedding.py            OpenAI embedding wrapper
    indexer.py              Writes Postgres document_chunks + Chroma vectors
    pipeline.py             CLI: ingest metadata + PDFs
  retrieval/
    vector_store.py, keyword_search.py, fusion.py, reranker.py, retriever.py
    representative.py       Representative-chunk sampling for summarize/extract/compare
  llm/
    providers/              OpenAI + Gemini provider implementations
    router.py                Generation fallback routing
    prompts.py, generation.py  Prompt templates + citation parsing
  memory/                  preferences.py, history.py, recommender.py
  routers/                 One module per resource (search, papers, chat, compare, ...)
  services/                Business logic wiring routers ↔ db/retrieval/llm
  tests/unit/              pytest unit tests (parser, chunkers, fusion, citation parsing)
frontend/src/
  pages/                   Search, PaperDetail, Chat, Compare, Collections, Preferences, History
  components/, api/        Shared UI components, typed API client
experiments/chunking/      Chunking strategy experiment: ground truth, runner, REPORT.md
eval/                      Evaluation harness (in progress - see Status)
docker/                    docker-compose.yml
data/                      Downloaded PDFs + Chroma persistence (gitignored)
```

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop (for Postgres)
- An OpenAI API key, and optionally a Gemini API key for generation fallback

### 1. Configure environment

```bash
cp .env.example .env
# edit .env: set OPENAI_API_KEY (required) and GEMINI_API_KEY (optional fallback)
```

### 2. Start Postgres

```bash
docker compose -f docker/docker-compose.yml up -d postgres
```

### 3. Backend setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
alembic upgrade head
```

### 4. Ingest papers and build the index

```bash
# Fetch metadata + PDFs from arXiv (adjust categories/volume as desired)
python -m app.ingestion.pipeline --categories cs.AI,cs.CV,cs.LG,stat.ML --max-per-category 150

# Chunk + embed into Postgres and Chroma using the winning parent_child strategy
python -m app.ingestion.indexer
```

### 5. Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### 6. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

### Running tests

```bash
cd backend
pytest app/tests/unit -v
```

## Project status

This is being built end-to-end from the original brief. Current state:

- [x] arXiv ingestion pipeline (metadata + PDF download, rate-limited, idempotent)
- [x] Section-aware PDF parsing with page-accurate citation tracking
- [x] All 4 chunking strategies implemented and experimentally compared
- [x] Production indexing (Postgres + Chroma)
- [x] Hybrid retrieval (dense + sparse fusion) with cross-encoder reranking
- [x] LLM generation layer with provider fallback and citation parsing
- [x] FastAPI backend covering all 10 product features
- [x] React frontend (Search, Paper detail, Chat, Compare, Collections, Preferences, History)
- [ ] Personalization: preference-weighted search ranking, engagement-based recommendations
- [ ] Full evaluation harness (100 questions, 7 metrics, notebook)
- [ ] Full Docker Compose stack (backend + frontend containers, currently Postgres only)
- [ ] Technical report

## Known limitations

- PDF section detection is heuristic (font-size/heading pattern matching), not a dedicated
  scholarly-PDF parser — unusual paper layouts may be misclassified.
- No OCR — scanned/image-only PDFs are skipped rather than indexed.
- This is a single-user application by design; the `users` table exists for schema completeness,
  not multi-tenant auth.
- Chunking-experiment ground truth is LLM-drafted and excerpt-verified programmatically, with a
  human spot-check on a sample rather than full manual verification of every question.
