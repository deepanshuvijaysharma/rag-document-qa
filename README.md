# RAG Document Q&A Engine

[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.2-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F61?style=flat-square)](https://docs.trychroma.com)
[![Tests Passing](https://img.shields.io/badge/Tests-74%2F74_Passed-success?style=flat-square)](file:///d:/rag-document-qa/RAG_EVALUATION.md)

An enterprise-grade, production-hardened **Retrieval-Augmented Generation (RAG)** Document Question-Answering platform. Built with Python 3.13, FastAPI, PyMuPDF, SentenceTransformers (`all-MiniLM-L6-v2`), ChromaDB, and React 19 + Tailwind CSS.

Designed for high reliability, strict groundedness compliance, prompt-injection defense, Server-Sent Events (SSE) streaming, and verifiable page-level citation tracing.

---

## Overview

The **RAG Document Q&A Engine** enables users to upload PDF documents, automatically index semantic text chunks into a local vector database, and ask natural language questions against their knowledge base. 

Rather than sending raw documents directly to an LLM, the system performs **cosine similarity vector retrieval** in ChromaDB to retrieve only the top $K$ relevant text chunks, wraps them in untrusted context demarcation tags, and instructs a provider-agnostic LLM (OpenAI, Groq, Anthropic, or local Ollama) to generate **verifiable answers backed by 1-indexed page citations**.

If the uploaded knowledge base does not contain the answer, the engine explicitly returns a grounded fallback message: `"I am unable to find the answer in the uploaded documents."`

---

## Features

- 📄 **PDF Document Ingestion**: Validates PDF file extension, `%PDF-` magic header bytes, MIME types, 0-byte detection, and max page boundaries (500 pages / 25MB limit).
- 🧩 **Semantic Text Chunking**: Recursive character text splitting (`chunk_size=1000`, `chunk_overlap=200`) preserving 1-indexed page numbers, chunk indexes, and source filenames.
- ⚡ **Dense Vector Embeddings**: Local `SentenceTransformers` (`all-MiniLM-L6-v2`, 384 dimensions) batch embedding without external API dependency.
- 🗄️ **ChromaDB Vector Store**: Embedded persistent vector collection (`hnsw:space="cosine"`) with atomic rollback safety and document purging on deletion.
- 🔍 **Cosine Similarity Search**: Normalized distance vector retrieval with optional document-id filtering and relevance thresholding ($\ge 0.35$).
- 🛡️ **Defensive Prompt Injection Guardrails**: Treats retrieved document text as untrusted data. Demarcated context blocks prevent embedded malicious directives (`"Ignore previous instructions"`) from overriding system behavior.
- ⚡ **Real-Time SSE Streaming**: Progressive token streaming (`POST /api/chat/stream`) via Server-Sent Events with typing cursor indicators.
- 📍 **Page-Level Source Citations**: Every response returns interactive source cards with filename, 1-indexed page number, similarity percentage badge, and click-to-expand text snippet drawers.
- 🤖 **Provider-Agnostic LLM Layer**: Unified adapter supporting OpenAI (`gpt-4o-mini`), Groq, Anthropic, and local Ollama without code changes.
- 💬 **Multi-Turn Conversation Persistence**: Thread-safe persistent session history (`data/conversations.json`) for contextual Q&A continuity.
- 🎨 **Modern React 19 Dashboard**: Glassmorphism UI with Tailwind CSS v4, document sidebar, scope filtering, dark mode, and responsive layout.

---

## System Architecture

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 REACT 19 FRONTEND                                 │
│        (Vite + Tailwind CSS v4 • Document Sidebar • SSE Chat Window)             │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │  REST / SSE HTTP Streaming
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI BACKEND ENGINE                              │
│                                                                                   │
│  ┌───────────────────────┐   ┌────────────────────────┐   ┌────────────────────┐ │
│  │ DocumentService       │   │ ChunkingService        │   │ EmbeddingService   │ │
│  │ (PDF Validation)      │──►│ (Recursive Splitter)   │──►│ (MiniLM-L6-v2 384d)│ │
│  └───────────────────────┘   └────────────────────────┘   └─────────┬──────────┘ │
│                                                                     │            │
│                                                                     ▼            │
│  ┌───────────────────────┐   ┌────────────────────────┐   ┌────────────────────┐ │
│  │ LLMService            │   │ ChatService            │   │ VectorService      │ │
│  │ (OpenAI/Groq/Ollama)  │◄──│ (Grounded RAG Pipeline)│◄──│ (ChromaDB Cosine)  │ │
│  └───────────────────────┘   └────────────────────────┘   └────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Core Framework**: Python 3.13, FastAPI 0.115, Uvicorn
- **PDF Extraction**: PyMuPDF (`fitz` 1.25)
- **Text Chunking**: LangChain Text Splitters (`RecursiveCharacterTextSplitter`)
- **Vector Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`)
- **Vector Storage**: ChromaDB (`chromadb` 0.6.3, HNSW Cosine Index)
- **LLM Integrations**: OpenAI, Groq, Anthropic, Ollama (`httpx` Async)
- **Data Validation**: Pydantic v2 & Pydantic Settings
- **Testing Suite**: `pytest`, `pytest-asyncio`, `httpx`

### Frontend
- **Framework & Build**: React 19, Vite 6.2, JavaScript (ES2022)
- **Styling**: Tailwind CSS v4 (`@tailwindcss/vite`), Lucide React Icons
- **Markdown & Code**: `react-markdown` (Sanitized Virtual DOM rendering)
- **Deployment & Proxying**: Nginx Alpine multi-stage Docker build

---

## RAG Ingestion & Q&A Pipeline

```text
User PDF Upload
     ↓
File Validation (.pdf, %PDF-, MIME, 25MB, 500p)
     ↓
Text Extraction (PyMuPDF, 1-indexed pages)
     ↓
Text Chunking (Recursive Splitter: size=1000, overlap=200)
     ↓
Vector Embedding (SentenceTransformers 384d)
     ↓
Vector Indexing (ChromaDB HNSW Cosine Space)
     ↓
User Natural Language Question
     ↓
Query Embedding (SentenceTransformers)
     ↓
Vector Similarity Search (ChromaDB Top 4 Matches)
     ↓
Relevance Score Threshold Evaluation (≥ 0.35)
     │
     ├─► Below Threshold ──► Grounded Fallback Answer ("I am unable to find...")
     │
     └─► Above Threshold ──► Assemble Untrusted Context Block
                                   ↓
                             Prompt Guardrails & Conversation History
                                   ↓
                             LLM Generation (Streaming SSE Tokens)
                                   ↓
                             Extract Page Citations & Excerpt Snippets
                                   ↓
                             Return Answer + Interactive Source Cards
```

---

## API Endpoints

| Method | Endpoint | Description | Payload / Response |
|---|---|---|---|
| `GET` | `/health` | Server Health Status | `{"status": "ok"}` |
| `POST` | `/api/documents/upload` | Ingest PDF document | Multipart form `file`; returns `document_id`, `page_count`, `chunk_count` |
| `GET` | `/api/documents` | List active documents | Returns array of ingested PDF document records |
| `GET` | `/api/documents/{id}` | Get document details | Returns document metadata, page list, and text chunks |
| `DELETE` | `/api/documents/{id}` | Purge document & vectors | Deletes document record and purges ChromaDB vectors |
| `POST` | `/api/retrieval/search` | Search vector chunks | JSON `{query, top_k, document_id}`; returns similarity matches |
| `POST` | `/api/chat` | Non-streaming RAG Q&A | JSON `{message, document_id, conversation_id}`; returns answer & citations |
| `POST` | `/api/chat/stream` | SSE Streaming RAG Q&A | JSON `{message, document_id}`; streams `metadata`, `token`, `done` events |

*Full endpoint specifications are documented in [`API.md`](file:///d:/rag-document-qa/API.md).*

---

## Environment Variables

Copy `.env.example` to `.env` in the root directory:

```env
# Application Settings
APP_ENV=development
API_PREFIX=/api/v1

# LLM Provider Selection (options: openai, ollama, groq, anthropic)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Provider API Keys (Never commit actual keys!)
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434

# Ingestion & Retrieval Boundaries
MAX_UPLOAD_SIZE_MB=25
MAX_DOCUMENT_PAGES=500
TOP_K=4
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

---

## Local Setup & Development

### Prerequisites
- Python 3.13 or Python 3.11+
- Node.js 20+ & npm
- Git

### 1. Clone Repository
```bash
git clone https://github.com/your-username/rag-document-qa.git
cd rag-document-qa
```

### 2. Setup Backend Virtual Environment
```bash
cd backend
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup Environment File
```bash
cp ../.env.example .env
```

### 4. Start Backend Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API docs are available at `http://127.0.0.1:8000/api/v1/docs`.*

### 5. Setup & Start Frontend
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Frontend dev server serves at `http://localhost:5173`.*

---

## Docker Setup

Deploy the entire stack (FastAPI backend + Nginx React frontend + ChromaDB persistent volumes) using Docker Compose:

```bash
# Build and launch containers
docker compose up --build -d

# Verify container status
docker compose ps

# View backend logs
docker compose logs -f backend
```
- Access Frontend UI at `http://localhost:5173` (or `http://localhost`).
- Access Backend API at `http://localhost:8000`.

---

## Testing & Verification

Run the full automated test suite covering unit tests, integration routes, security guardrails, and benchmark evaluation:

```bash
cd backend
python -m pytest -v
```

**Test Results Summary**:
```text
============================= 74 passed in 10.87s ==============================
```

---

## RAG Evaluation Benchmark

The platform includes an automated quantitative benchmark dataset ([`backend/app/tests/evaluation/rag_evaluation_dataset.json`](file:///d:/rag-document-qa/backend/app/tests/evaluation/rag_evaluation_dataset.json)) measuring retrieval hit rate, citation precision, and grounded fallback compliance.

*Read the complete benchmark report in [`RAG_EVALUATION.md`](file:///d:/rag-document-qa/RAG_EVALUATION.md).*

---

## Security & Reliability Controls

- **Path Traversal Sanitization**: Directory path components (`../../`) and null bytes are stripped via `os.path.basename` and regex regex filtering.
- **Prompt Injection Defense**: Retrieved document context is wrapped in `--- UNTRUSTED RETRIEVED DOCUMENT CONTEXT START ---` tags with explicit guardrails instructing the LLM to ignore embedded commands.
- **Secret Protection**: Sensitive API keys are masked (`sk-p...2345`) in logs and representations and are never sent to the React frontend client.
- **Error Leakage Prevention**: Custom global exception handlers return sanitized HTTP 500 responses without exposing internal Python tracebacks or file paths.

*Read the detailed security architecture in [`SECURITY.md`](file:///d:/rag-document-qa/SECURITY.md).*

---

## Current Limitations

- **Scanned / Image PDFs**: PyMuPDF extracts embedded text layers. PDFs containing scanned images without OCR layers yield empty text warnings.
- **Single-Node Vector Store**: Uses embedded ChromaDB with SQLite persistence, which is suitable for single-node deployments but requires distributed ChromaDB or PostgreSQL `pgvector` for multi-node horizontal scaling.

---

## Future Improvements

- 🔎 **Hybrid Search (BM25 + Dense Vectors)**: Combine keyword BM25 search with dense vector embeddings for enhanced domain jargon retrieval.
- 🎯 **Cross-Encoder Reranking**: Re-rank top $K$ retrieved vector chunks using Cohere or BGE Reranker before LLM context construction.
- 🔐 **Production Auth & Multi-Tenancy**: Add OAuth2 JWT authentication and tenant-isolated vector collection metadata filters.
- 🐘 **PostgreSQL & `pgvector`**: Migration path for production relational metadata storage and vector indexing.
