# Paperlight — AI Research Paper Summarizer

Upload research papers as PDFs and get instant AI-generated summaries, ask grounded
questions about the content (RAG), and auto-generate study materials — all backed by
Google Gemini 2.5 Flash.

![status](https://img.shields.io/badge/backend-FastAPI-009688) ![status](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-3178C6) ![status](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4)

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Folder Structure](#folder-structure)
5. [Installation](#installation)
6. [Environment Variables](#environment-variables)
7. [Running the App](#running-the-app)
8. [API Documentation](#api-documentation)
9. [Sample Papers](#sample-papers)
10. [Deployment Guide](#deployment-guide)
11. [Screenshots](#screenshots)
12. [Dependency List](#dependency-list)

---

## Features

- **Upload** — drag-and-drop, multi-file, upload progress, 25MB limit, PDF validation
- **Automatic analysis** — executive summary, abstract summary, key contributions,
  methodology, results, limitations, future work, keywords, equations, figures, reference count
- **AI Chat (RAG)** — ask natural-language questions; every answer includes the
  source **page number**, a supporting **citation snippet**, and a **confidence score**,
  grounded strictly in the uploaded paper (no outside knowledge)
- **Study notes** — exam notes, flashcards (flip-card UI), bullet notes, interview
  questions, viva questions, and 10 MCQs with instant right/wrong feedback
- **Semantic search** — search across all uploaded papers, ranked by relevance
- **Dashboard** — papers uploaded, total pages, chat history count, recent uploads, favorites
- **Export** — download the summary, study notes, or flashcards as a PDF
- **Bonus features** — Recent Papers, Favorite Papers, Reading Progress, Copy AI
  Response, Download Chat history
- **UI** — shadcn/ui-style component system, dark mode, toast notifications, loading
  skeletons, responsive layout, Markdown rendering in chat answers

---

## Tech Stack

| Layer      | Technology                                                                 |
|------------|-----------------------------------------------------------------------------|
| Frontend   | React 19, TypeScript, Vite, Tailwind CSS v4, Radix UI (shadcn/ui primitives) |
| Backend    | FastAPI, Python 3.12                                                        |
| AI         | Google Gemini 2.5 Flash (`google-genai` SDK), LangChain (text chunking)     |
| Embeddings | `fastembed` (ONNX runtime, `sentence-transformers/all-MiniLM-L6-v2` model)  |
| Vector DB  | FAISS (per-paper flat inner-product index)                                 |
| Database   | SQLite (via SQLAlchemy ORM)                                                |
| PDF        | `pypdf` (extraction), `reportlab` (export)                                 |

> **Note on embeddings:** the spec calls for `sentence-transformers`. This project uses
> `fastembed`, which runs the *same* `all-MiniLM-L6-v2` sentence-transformers model but
> through ONNX Runtime instead of PyTorch. Functionally and qualitatively identical
> results, without a multi-gigabyte PyTorch+CUDA install. If you'd prefer the literal
> `sentence-transformers` package, swap `app/services/vector_store.py`'s embedding
> calls for `SentenceTransformer(...).encode(...)` — the rest of the RAG pipeline is unchanged.

---

## Architecture

```
┌─────────────┐      HTTP/JSON       ┌──────────────────┐
│   React SPA │ ───────────────────► │   FastAPI (v1)   │
│  (Vite/TS)  │ ◄─────────────────── │                  │
└─────────────┘                      └────────┬─────────┘
                                               │
                     ┌─────────────────────────┼─────────────────────────┐
                     ▼                         ▼                         ▼
             ┌───────────────┐        ┌────────────────┐        ┌───────────────┐
             │  SQLite (ORM) │        │  FAISS indexes  │        │  Gemini 2.5   │
             │  papers, chat,│        │  (per paper,    │        │  Flash API    │
             │  study notes  │        │  on disk)       │        │  (google-genai)│
             └───────────────┘        └────────────────┘        └───────────────┘
```

**Upload → Processing pipeline** (runs as a FastAPI `BackgroundTask` so the upload
request returns immediately):

1. `uploaded` — file validated (PDF header, size ≤ 25MB) and saved to disk
2. `extracting` — text pulled per-page with `pypdf`
3. `indexing` — text is chunked (LangChain `RecursiveCharacterTextSplitter`), embedded,
   and written to a per-paper FAISS index (so RAG chat and search work immediately,
   even before Gemini's summary finishes)
4. `analyzing` — Gemini produces the structured JSON analysis (summary, contributions,
   methodology, etc.) which is parsed and persisted to SQLite
5. `ready` — all features (chat, notes, export) become available
6. `failed` — any exception in the pipeline is caught and stored as `error_message`,
   visible in the UI, so a bad PDF or missing API key never leaves the app hanging

All blocking AI/embedding calls run via `asyncio.to_thread` so the server's event loop
(and `/health` endpoint) stays responsive even while a large paper is mid-processing.

---

## Folder Structure

```
research-summarizer/
├── server/                        # FastAPI backend
│   ├── app/
│   │   ├── main.py                # app entrypoint, CORS, startup, error handler
│   │   ├── core/
│   │   │   ├── config.py          # pydantic-settings, env vars
│   │   │   └── database.py        # SQLAlchemy engine/session
│   │   ├── models/                # Paper, ChatMessage, StudyNote (SQLAlchemy)
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── pdf_service.py      # PDF validation + text extraction
│   │   │   ├── vector_store.py     # chunking + FAISS + fastembed
│   │   │   ├── gemini_service.py   # Gemini prompts (analysis, RAG, notes)
│   │   │   ├── analysis_service.py # orchestrates the processing pipeline
│   │   │   └── export_service.py   # reportlab PDF generation
│   │   └── api/v1/
│   │       ├── papers.py           # upload, list, favorite, progress, delete
│   │       ├── chat.py             # RAG ask + history
│   │       ├── notes.py            # study notes generate/get
│   │       ├── search.py           # semantic search
│   │       ├── dashboard.py        # aggregate stats
│   │       ├── export.py           # PDF downloads
│   │       └── router.py           # aggregates all routers under /api/v1
│   ├── storage/
│   │   ├── app.db                  # SQLite database (created on first run)
│   │   ├── faiss_index/            # per-paper FAISS indexes
│   │   └── samples/                # sample research paper PDFs
│   ├── uploads/                    # uploaded PDF files
│   ├── requirements.txt
│   └── .env.example
│
├── client/                        # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                 # Button, Card, Badge, Tabs, Dialog, Toast, etc.
│   │   │   ├── layout/             # AppLayout (sidebar/topbar), PageHeader
│   │   │   └── paper/              # PaperCard, StatusBadge, OverviewTab, ChatTab, StudyNotesTab
│   │   ├── pages/                  # DashboardPage, UploadPage, PaperDetailPage, SearchPage
│   │   ├── context/                # ThemeContext (dark mode)
│   │   ├── hooks/                  # usePaperStatusPolling
│   │   ├── lib/                    # api.ts (axios client), utils.ts
│   │   └── types/                  # shared TypeScript interfaces
│   ├── index.html
│   ├── vite.config.ts
│   └── .env.example
│
└── docs/
    └── (this README)
```

---

## Installation

### Prerequisites

- Python 3.12 or 3.13 (all pinned dependencies ship prebuilt Windows wheels for both — no C++ build tools needed)
- Node.js 20+ and npm
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free tier available)

### 1. Clone / unzip the project

```bash
cd research-summarizer
```

### 2. Backend setup

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_real_key_here
```

#### Windows (PowerShell)

```powershell
cd server
py -3.13 -m venv .venv            # or: py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope Process Bypass
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check

Copy-Item .env.example .env
# Edit .env and set GEMINI_API_KEY (never commit .env)
```

In VS Code: `Ctrl+Shift+P` -> **Python: Select Interpreter** -> `server\.venv\Scripts\python.exe`.

Run the tests (the Gemini call and embedding-model download are stubbed; everything else is real):

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

> The first real upload downloads the ~90 MB MiniLM embedding model from Hugging Face
> (cached afterwards). Set `FASTEMBED_CACHE_DIR` to control where it is stored.

### 3. Frontend setup

```bash
cd ../client
npm install
cp .env.example .env
# Defaults to http://localhost:8000 — change VITE_API_URL if your backend runs elsewhere
```

---

## Environment Variables

**`server/.env`**

| Variable                 | Description                                   | Default                  |
|---------------------------|-----------------------------------------------|---------------------------|
| `GEMINI_API_KEY`           | **Required.** Your Google Gemini API key      | *(empty — must be set)*   |
| `GEMINI_MODEL`             | Gemini model name                             | `gemini-2.5-flash`        |
| `ENVIRONMENT`              | `development` or `production`                 | `development`              |
| `DEBUG`                    | Enable debug logging                          | `true`                     |
| `CORS_ORIGINS`             | JSON array of allowed frontend origins        | `["http://localhost:5173"]`|
| `FASTEMBED_CACHE_DIR`      | Optional folder for the embedding-model cache | *(system temp dir)*        |

**`client/.env`**

| Variable        | Description                       | Default                 |
|-----------------|------------------------------------|--------------------------|
| `VITE_API_URL`  | Base URL of the FastAPI backend    | `http://localhost:8000` |

> **Security note:** API keys are only ever read from environment variables — never
> hardcoded. `.env` files are git-ignored by default.

---

## Running the App

**Terminal 1 — backend:**

```bash
cd server
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at `http://localhost:8000`. Interactive Swagger docs at
`http://localhost:8000/api/docs` (ReDoc at `/api/redoc`).

**Terminal 2 — frontend:**

```bash
cd client
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Verify everything works

```bash
curl http://localhost:8000/health
# {"status":"ok","app":"AI Research Paper Summarizer"}
```

Then open `http://localhost:5173`, go to **Upload**, and drop in one of the sample
PDFs from `server/storage/samples/`.

### Building for production

```bash
# Frontend
cd client
npm run build        # outputs to client/dist/

# Backend (no build step — run directly with a production ASGI server)
cd server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API Documentation

All endpoints are versioned under `/api/v1`. Full interactive documentation (with
request/response schemas and a "try it out" button) is auto-generated by FastAPI at
**`/api/docs`**.

| Method | Endpoint                              | Description                                |
|--------|----------------------------------------|---------------------------------------------|
| POST   | `/api/v1/papers/upload`                | Upload a single PDF                          |
| POST   | `/api/v1/papers/upload-multiple`       | Upload multiple PDFs                         |
| GET    | `/api/v1/papers`                       | List all papers                              |
| GET    | `/api/v1/papers/{id}`                  | Get full analysis for a paper                |
| GET    | `/api/v1/papers/{id}/status`           | Poll processing status                       |
| PATCH  | `/api/v1/papers/{id}/favorite`         | Toggle favorite                              |
| PATCH  | `/api/v1/papers/{id}/progress`         | Update reading progress                      |
| POST   | `/api/v1/papers/{id}/open`             | Mark as recently opened                      |
| DELETE | `/api/v1/papers/{id}`                  | Delete a paper and its data                  |
| POST   | `/api/v1/chat/{id}/ask`                | Ask a RAG-grounded question                  |
| GET    | `/api/v1/chat/{id}/history`            | Get chat history for a paper                 |
| GET    | `/api/v1/chat/history/all`             | Get chat history across all papers           |
| POST   | `/api/v1/notes/{id}/generate`          | Generate study notes                         |
| GET    | `/api/v1/notes/{id}`                   | Get previously generated study notes         |
| POST   | `/api/v1/search`                       | Semantic search across all papers            |
| POST   | `/api/v1/search/{id}`                  | Semantic search within one paper             |
| GET    | `/api/v1/dashboard`                    | Aggregate stats for the dashboard            |
| GET    | `/api/v1/export/{id}/summary`          | Download summary as PDF                      |
| GET    | `/api/v1/export/{id}/study-notes`      | Download study notes as PDF                  |
| GET    | `/api/v1/export/{id}/flashcards`       | Download flashcards as PDF                   |
| GET    | `/health`                              | Health check                                 |

---

## Sample Papers

Two realistic sample research papers (generated with `reportlab`, not real published
work) are included for testing in `server/storage/samples/`:

- `attention_mechanisms_survey.pdf` — a survey-style ML paper (attention mechanisms)
- `federated_learning_healthcare.pdf` — an applied ML paper (federated learning)

Both include an abstract, numbered sections (introduction, methodology, results,
limitations, future work), and a references list — enough structure to exercise every
analysis field.

---

## Deployment Guide

### Backend (e.g. Render, Railway, Fly.io, a VPS)

1. Set `GEMINI_API_KEY` and `CORS_ORIGINS` (pointing at your deployed frontend URL) as
   environment variables on the host.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run with a production ASGI server: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4`.
4. Mount `server/storage/` and `server/uploads/` on a persistent volume — SQLite, the
   FAISS indexes, and uploaded PDFs all live there. For multi-instance deployments,
   swap SQLite for Postgres and FAISS-on-disk for a managed vector DB (e.g. Pinecone,
   Qdrant Cloud) — the service layer (`vector_store.py`) is the only place that needs
   to change.

### Frontend (e.g. Vercel, Netlify, Cloudflare Pages)

1. Set `VITE_API_URL` to your deployed backend's URL as a build-time environment variable.
2. Build command: `npm run build`. Output directory: `dist/`.
3. Since this is a client-side-routed SPA (`react-router-dom`), configure a rewrite/
   fallback rule so all paths serve `index.html` (e.g. a `_redirects` file with
   `/*  /index.html  200` on Netlify, or the default SPA fallback on Vercel).

### Docker (optional, backend)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Screenshots

_The UI includes: a Dashboard with stat cards and recent/favorite papers, a
drag-and-drop Upload screen with per-file progress, a Paper Detail view with
Overview/Chat/Study-Notes tabs, RAG chat answers with page-citation "marginalia"
cards and confidence meters, flip-animation flashcards, instant-feedback MCQs, and a
cross-paper semantic Search screen — all in both light and dark mode._

To capture your own screenshots: run the app locally (see [Running the App](#running-the-app)),
upload a sample paper, and screenshot the Dashboard, Paper Detail (each tab), and
Search pages.

---

## Dependency List

### Backend (`server/requirements.txt`)

```
fastapi, uvicorn[standard], python-multipart, sqlalchemy, pydantic,
pydantic-settings, python-dotenv, pypdf, google-genai,
langchain-text-splitters, faiss-cpu, fastembed, reportlab, markdown, aiofiles
```

### Frontend (`client/package.json`)

```
react, react-dom, react-router-dom, axios, react-markdown, remark-gfm,
clsx, tailwind-merge, lucide-react, class-variance-authority,
@radix-ui/react-tabs, @radix-ui/react-dialog, @radix-ui/react-switch,
@radix-ui/react-progress, @radix-ui/react-label, @radix-ui/react-dropdown-menu,
@radix-ui/react-avatar, tailwindcss v4, @tailwindcss/vite, @tailwindcss/typography,
typescript, vite
```

---

## License

MIT — do whatever you'd like with this project. Built as a portfolio-ready,
production-structured full-stack AI application.
