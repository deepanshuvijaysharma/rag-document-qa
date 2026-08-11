# RAG Document Q&A - Backend Service

Production-style Python FastAPI backend service handling document parsing, vector indexing, retrieval-augmented generation (RAG), and streaming response APIs.

---

## 1. Prerequisites

- **Python Version**: Python 3.11+ (Python 3.13 supported)
- **Virtual Environment Tool**: Standard `venv` or `conda`

---

## 2. Environment Setup & Virtual Environment

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell / Command Prompt)**:
     ```powershell
     .venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```

---

## 3. Dependency Installation

Install production and development dependencies into the activated virtual environment:

```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development & testing dependencies
pip install -r requirements-dev.txt
```

---

## 4. Environment Configuration

1. **Create local `.env` file from `.env.example` template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables in `.env`**:
   ```env
   APP_ENV=development
   APP_NAME="RAG Document Q&A"
   API_PREFIX="/api/v1"
   FRONTEND_ORIGIN="http://localhost:5173"

   CHROMA_PERSIST_DIRECTORY="./data/chroma"
   CHROMA_COLLECTION_NAME="rag_documents"

   EMBEDDING_MODEL="all-MiniLM-L6-v2"
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200

   LLM_PROVIDER="openai"
   LLM_MODEL="gpt-4o-mini"
   OPENAI_API_KEY="your_actual_api_key_here"
   ```

> **IMPORTANT**: Never commit your `.env` file to Git repository. `.env` is listed in `.gitignore`.

---

## 5. Running the Backend Server

Start the development server with live reload:

```bash
uvicorn app.main:app --reload --port 8000
```

### Accessing Interactive API Documentation
Once running, open your browser:
- **Root Health Check**: `http://localhost:8000/health`
- **API Health Check**: `http://localhost:8000/api/v1/health`
- **Swagger Interactive Docs**: `http://localhost:8000/api/v1/docs`
- **ReDoc Open API Specification**: `http://localhost:8000/api/v1/redoc`

---

## 6. Running Tests

Run backend automated test suite using `pytest`:

```bash
# Run all backend tests
pytest

# Run tests with detailed output
pytest -v

# Run specific test file
pytest app/tests/test_health.py
```
