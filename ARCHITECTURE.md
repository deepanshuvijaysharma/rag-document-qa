# System Architecture: RAG Document Q&A

## 1. High-Level Architecture Diagram

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    BROWSER (CLIENT)                    │
                               │  React + Vite + Tailwind CSS + Lucide Icons + Fetch    │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                            HTTP / REST   │   Server-Sent Events (SSE)
                                            Multipart/JSON│   Streaming Chat Response
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             FASTAPI BACKEND SERVICE                                         │
│                                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                       API ROUTER LAYER (v1)                                         │   │
│   │   POST /api/v1/documents/upload  │  GET /api/v1/documents  │ DELETE /api/v1/documents/{id}          │   │
│   │   POST /api/v1/chat/stream       │  GET /api/v1/health                                             │   │
│   └──────────────────────────────────┬──────────────────────────────────┬───────────────────────────────┘   │
│                                      │                                  │                                   │
│                                      ▼                                  ▼                                   │
│   ┌─────────────────────────────────────┐                            ┌──────────────────────────────────┐   │
│   │          DOCUMENT SERVICE           │                            │            RAG SERVICE           │   │
│   │  - File Validation & Magic Check    │                            │  - Context Retrieval Assembly    │   │
│   │  - PyMuPDF Page Text Parsing        │                            │  - Strict Groundedness Prompting │   │
│   │  - Metadata Tagging (doc_id, page)  │                            │  - SSE Chunk Streaming           │   │
│   └──────────────────┬──────────────────┘                            └──────────────────┬───────────────┘   │
│                      │                                                                  │                   │
│                      ▼                                                                  ▼                   │
│   ┌─────────────────────────────────────┐                            ┌──────────────────────────────────┐   │
│   │           TEXT PROCESSOR            │                            │           LLM SERVICE            │   │
│   │  - Normalization & Cleaning         │                            │  (Provider Abstraction Layer)    │   │
│   │  - RecursiveCharacterTextSplitter   │                            │  ├── OpenAI Adapter              │   │
│   │    (chunk_size=1000, overlap=200)   │                            │  ├── Ollama Adapter              │   │
│   └──────────────────┬──────────────────┘                            │  ├── Groq Adapter                │   │
│                      │                                               │  └── Anthropic Adapter           │   │
│                      ▼                                               └──────────────────────────────────┘   │
│   ┌─────────────────────────────────────┐                                                                   │
│   │          EMBEDDING SERVICE          │                                                                   │
│   │  - SentenceTransformers             │                                                                   │
│   │    (all-MiniLM-L6-v2, 384-dim)      │                                                                   │
│   └──────────────────┬──────────────────┘                                                                   │
│                      │                                                                                      │
│                      ▼                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                      VECTOR SERVICE (ChromaDB)                                      │   │
│   │  - Collection Management  │  Embedding Persistence  │  Cosine Distance Similarity Search          │   │
│   └──────────────────────────────────────────────┬──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
                                 ┌───────────────────────────────────┐
                                 │       PERSISTENT VECTOR STORE     │
                                 │    ChromaDB Local Storage Volume  │
                                 └───────────────────────────────────┘
```

---

## 2. Directory & Folder Structure

```
rag-document-qa/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── documents.py       # Upload, list, delete document endpoints
│   │   │   │   │   ├── chat.py            # Streaming Q&A endpoints
│   │   │   │   │   └── health.py          # Liveness and readiness health checks
│   │   │   │   └── router.py              # Aggregated v1 API router
│   │   ├── core/
│   │   │   ├── config.py                  # Pydantic Settings (.env configuration management)
│   │   │   ├── logging.py                 # Structured JSON logging framework
│   │   │   └── exceptions.py              # Custom domain exception handlers
│   │   ├── db/
│   │   │   └── chroma_client.py           # Persistent ChromaDB client singleton wrapper
│   │   ├── schemas/
│   │   │   ├── document.py                # Document upload, list, metadata Pydantic models
│   │   │   └── chat.py                    # Chat request, response, citation Pydantic models
│   │   ├── services/
│   │   │   ├── document_service.py        # File validation and PyMuPDF text parser
│   │   │   ├── text_processor.py          # Clean, sanitize, and recursive chunking logic
│   │   │   ├── embedding_service.py       # SentenceTransformers embedding generator wrapper
│   │   │   ├── vector_service.py          # ChromaDB collection CRUD & similarity queries
│   │   │   ├── llm_service.py             # LLM Factory & provider adapters (OpenAI, Ollama, etc.)
│   │   │   └── RAG_service.py             # RAG pipeline orchestration (Retrieve -> Prompt -> Stream)
│   │   └── main.py                        # FastAPI application entrypoint & middleware configuration
│   ├── tests/
│   │   ├── test_document_service.py       # PyMuPDF parser unit tests
│   │   ├── test_text_processor.py         # Chunking and metadata preservation tests
│   │   ├── test_rag_service.py            # Retrieval and citation generation tests
│   │   └── test_api.py                    # Endpoint integration tests via AsyncClient
│   ├── Dockerfile                         # Python 3.11 slim backend container definition
│   ├── requirements.txt                   # Backend dependencies
│   └── pytest.ini                         # Pytest test runner configuration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/                    # Header, Footer, Status Badges, Modal dialogs
│   │   │   ├── documents/                 # FileDropzone, DocumentList, DocumentItem
│   │   │   ├── chat/                      # ChatBox, MessageList, MessageItem, PromptInput
│   │   │   └── citations/                 # CitationList, CitationCard, PageBadge
│   │   ├── hooks/
│   │   │   ├── useDocuments.js            # Custom hook for document upload & listing state
│   │   │   └── useChat.js                 # Custom hook for streaming SSE chat state
│   │   ├── services/
│   │   │   └── api.js                     # Fetch API client for backend endpoints
│   │   ├── types/                         # JSDoc type definitions for data structures
│   │   ├── utils/                         # Formatter helpers (file size, date, page label)
│   │   ├── App.jsx                        # Application root layout & layout grid
│   │   ├── main.jsx                       # React DOM entrypoint
│   │   └── index.css                      # Base styles & Tailwind directives
│   ├── public/                            # Static assets & favicon
│   ├── Dockerfile                         # Multi-stage Docker build for React + Nginx
│   ├── package.json                       # Frontend dependencies & scripts
│   ├── vite.config.js                     # Vite build configuration & API proxy rule
│   └── tailwind.config.js                 # Tailwind design token configuration
├── docker-compose.yml                     # Multi-container orchestration file
├── PROJECT_PLAN.md                        # Master project plan & execution roadmap
├── ARCHITECTURE.md                        # System architecture & sequence design specification
└── README.md                              # Repository overview & setup guide
```

---

## 3. Component Responsibilities

| Component Layer | Module / File | Responsibility |
|---|---|---|
| **API Router** | `api/v1/endpoints/` | Validates HTTP payloads using Pydantic, delegates work to services, handles HTTP status codes. |
| **Document Service** | `services/document_service.py` | Validates file MIME/magic header, uses `PyMuPDF` (`fitz`) to extract raw text page by page with page index tracking. |
| **Text Processor** | `services/text_processor.py` | Sanitizes raw text, applies `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200), attaches page metadata. |
| **Embedding Service** | `services/embedding_service.py` | Loads `SentenceTransformers` model (`all-MiniLM-L6-v2`), generates 384-dimensional vector embeddings for text chunks and queries. |
| **Vector Service** | `services/vector_service.py` | Interfaces with `ChromaDB`, manages collection indexing, executes similarity searches, purges vectors by `doc_id`. |
| **LLM Service** | `services/llm_service.py` | Factory pattern providing standardized interface (`generate_stream()`) across LLM providers (OpenAI, Ollama, Groq, Anthropic). |
| **RAG Service** | `services/rag_service.py` | Orchestrates query embedding $\rightarrow$ vector retrieval $\rightarrow$ prompt context assembly $\rightarrow$ LLM generation $\rightarrow$ citation extraction. |
| **Frontend State Hooks**| `hooks/useChat.js` & `useDocuments.js` | Manages active document lists, handle drag-and-drop uploads, consume SSE stream buffers, update chat thread state. |

---

## 4. End-to-End Execution Flows

### A. Document Upload & Ingestion Flow

```
[User] ──(Selects PDF)──► [FileDropzone.jsx]
                                │
                        (HTTP POST multipart/form-data)
                                │
                                ▼
                   [api/v1/endpoints/documents.py]
                                │
                                ├─► 1. File Validation (Extension check, Magic bytes %PDF-, Max 25MB)
                                │
                                ├─► 2. Document Service (PyMuPDF)
                                │       └─ Extract pages: [{page_no: 1, text: "..."}, {page_no: 2, text: "..."}]
                                │
                                ├─► 3. Text Processor
                                │       ├─ Clean text & remove noise
                                │       └─ Chunk via RecursiveCharacterTextSplitter
                                │          └─ Result: Chunks with metadata (doc_id, filename, page_number)
                                │
                                ├─► 4. Embedding Service
                                │       └─ Generate 384-dim embeddings for all chunks via SentenceTransformers
                                │
                                ├─► 5. Vector Service (ChromaDB)
                                │       └─ Upsert vectors, texts, and metadata into Chroma collection
                                │
                                ▼
[User UI] ◄──(JSON Response: {doc_id, filename, pages, chunks})── [FastAPI Router]
```

---

### B. Document Retrieval & Q&A Generation Flow (RAG)

```
[User] ──(Enters Question)──► [ChatBox.jsx]
                                │
                        (HTTP POST /api/v1/chat/stream)
                                │
                                ▼
                    [api/v1/endpoints/chat.py]
                                │
                                ▼
                   [services/rag_service.py]
                                │
                                ├─► 1. Embedding Service: Generate vector for user question
                                │
                                ├─► 2. Vector Service (ChromaDB):
                                │       └─ Similarity Search: Query Top-K (K=4) closest vectors
                                │       └─ Filter by relevance distance threshold
                                │
                                ├─► 3. Context Builder & Groundedness Check:
                                │       ├─ IF no chunks retrieved or score < threshold:
                                │       │   └─ Fast-return: "Information not found in uploaded documents."
                                │       └─ ELSE:
                                │           └─ Assemble Context Block:
                                │              "--- Page X of Document Y --- \n {chunk_text}"
                                │
                                ├─► 4. Prompt Formatter:
                                │       └─ Inject Context Block into Strict Grounded System Prompt
                                │
                                ├─► 5. LLM Service (Provider Adapter):
                                │       └─ Stream tokens asynchronously using SSE (Server-Sent Events)
                                │
                                ├─► 6. Citation Resolver:
                                │       └─ Build citation payload [{doc_name, page_number, snippet_preview}]
                                │
                                ▼
[User UI] ◄──(SSE Token Stream + Citations JSON)── [FastAPI Stream]
```

---

### C. Source Citation Flow

1. When ChromaDB completes similarity search, each returned result includes metadata:
   - `filename`: `"Financial_Report_2024.pdf"`
   - `page_number`: `14`
   - `snippet`: `"Q4 revenue grew by 18% year-over-year..."`
   - `distance`: `0.21` (Similarity Score: ~0.79)
2. The RAG service collects unique source metadata references during context assembly.
3. Before or immediately following the streaming response, a structured JSON event `{"event": "citations", "data": [...]}` is emitted to the client.
4. The React frontend renders collapsible **Source Citation Badges** (e.g. `📄 Financial_Report_2024.pdf (Page 14)`) underneath the generated answer. Clicking a badge expands a preview overlay of the exact context snippet.

---

### D. Document Deletion Flow

1. User clicks **Delete** on a document item in `DocumentList.jsx`.
2. Frontend calls `DELETE /api/v1/documents/{doc_id}`.
3. Backend `VectorService` executes ChromaDB collection query deletion where metadata `doc_id == target_doc_id`.
4. All associated document chunks and vector embeddings are permanently removed from the index.
5. Success response returns to frontend, updating the active document count and clearing any stale citations.

---

## 5. Error Handling & Edge Cases

| Failure Scenario | Component | Resolution / Fallback |
|---|---|---|
| Non-PDF file uploaded (.docx, .exe) | `DocumentService` | HTTP 400 Bad Request: `"Only valid PDF files are supported."` |
| Corrupt or password-protected PDF | `DocumentService` | Catch `fitz.FileDataError`, return HTTP 422: `"Unable to parse encrypted or damaged PDF."` |
| Empty PDF (scanned image only, no OCR) | `DocumentService` | Detect zero extracted characters, return HTTP 422: `"No extractable text found in PDF."` |
| Question out-of-scope / Not in docs | `RAGService` | Retrieval similarity check returns no match; system returns: `"I could not find information regarding this query in the uploaded documents."` |
| LLM Provider API Rate-Limited/Down | `LLMService` | Catch API exception, return SSE error event: `"LLM provider temporarily unavailable. Please verify API configuration."` |
| Vector Store Disk I/O Error | `VectorService` | Log critical alert, return HTTP 500 internal server error with non-sensitive user message. |

---

## 6. Security Considerations

1. **Secret & Key Management**:
   - Zero hardcoded keys or credentials anywhere in code.
   - All API keys (`OPENAI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`) loaded runtime from `.env` via Pydantic `BaseSettings`.
   - `.env` added to `.gitignore`. `.env.example` provided as clean template.
2. **File Upload Security**:
   - File extension AND magic number headers (`%PDF-`) verified before reading content into memory.
   - Filenames sanitized using standard filename path-traversal prevention helpers.
   - Max body size middleware enforced to prevent Denial of Service (DoS) memory exhaustion attacks.
3. **CORS & API Security**:
   - Strict CORS origin whitelisting configured in `FastAPI` middleware (`ALLOW_ORIGINS=["http://localhost:5173"]`).
   - Clean exception handling ensuring internal stack traces are never exposed to client HTTP responses.
