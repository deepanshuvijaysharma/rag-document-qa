# RAG Document Q&A

Production-style full-stack Retrieval-Augmented Generation (RAG) web application for PDF document processing, vector search, grounded answer generation, and precise source citations.

## Project Architecture

For comprehensive system specifications and architecture blueprints, refer to:
- [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — Implementation roadmap, user stories, development phases, and DoD.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — System architecture, ASCII diagrams, data flows, and security guidelines.
- [`.agents/rules/project-rules.md`](.agents/rules/project-rules.md) — Engineering rules and developer workflow guidelines.

## Quick Start (Skeleton Phase)

Currently, the application is in **Phase 1 (Skeleton Initialization)**.

### Environment Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (Phase 2+)
pip install -r requirements.txt
```

### Running Backend Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- Health Check: `http://localhost:8000/health`
- API Documentation: `http://localhost:8000/api/v1/docs`

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, PyMuPDF, SentenceTransformers, ChromaDB, LangChain
- **Frontend**: React, Vite, Tailwind CSS
- **Deployment**: Docker, Docker Compose
