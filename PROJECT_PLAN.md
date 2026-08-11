# Project Plan: RAG Document Q&A

## 1. Project Objective

**RAG Document Q&A** is a production-style, full-stack Retrieval-Augmented Generation (RAG) web application. It enables users to upload PDF documents, automatically process and index their contents into a vector database, and perform semantic question-answering strictly grounded in the uploaded documents. Every generated response includes precise source citations (document name and page number).

### Key Architectural Objectives
- **Strict Groundedness**: Uploaded documents are treated as the single source of truth. If the answer is absent from the retrieved chunks, the system explicitly responds that the information could not be found, preventing AI hallucinations.
- **Explainable GenAI Integration**: Concepts such as text extraction, chunking strategies, vector embeddings, similarity search, and context injection are clearly structured using clean design patterns.
- **Provider-Agnostic LLM Layer**: Complete abstraction over LLM providers (e.g., OpenAI, Ollama, Groq, Anthropic, HuggingFace) configured entirely via environment variables.
- **Production-Grade Engineering**: Strong separation of concerns, containerization, async streaming, comprehensive error handling, and end-to-end automated testing.

---

## 2. User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| **US-1** | User | Upload single or multiple PDF documents | I can build a custom knowledge base for my Q&A session. |
| **US-2** | User | View a list of processed documents with status & metadata | I know which documents are active, how many pages were parsed, and their status. |
| **US-3** | User | Delete a document from the system | Its vectors are purged from the vector database and no longer influence answers. |
| **US-4** | User | Ask natural language questions in a chat interface | I can retrieve precise answers from my uploaded documents. |
| **US-5** | User | See source citations with document name and page number | I can verify the exact location of the information within the original PDF. |
| **US-6** | User | Receive a clear "Information not found" message when appropriate | I am not misled by invented or hallucinated answers. |
| **US-7** | User | View streaming responses as the answer is generated | I get immediate feedback and a responsive UI experience. |
| **US-8** | Developer | Configure LLM models and embedding settings via environment variables | I can swap providers or run locally without modifying source code. |

---

## 3. Features & Functional Breakdown

### A. Document Processing & Ingestion Pipeline
1. **File Validation**:
   - Check file extensions (`.pdf`) and magic numbers (`%PDF-`).
   - Enforce maximum file size limits (default: 25 MB).
   - Prevent duplicate filenames or malicious path traversal names.
2. **Page-Preserving Text Extraction**:
   - Utilize `PyMuPDF` (`fitz`) for fast, robust PDF parsing.
   - Extract raw text per page while preserving `page_number` metadata (1-indexed).
3. **Text Cleaning & Normalization**:
   - Remove null characters, excess whitespace, broken line breaks, and page header/footer noise.
4. **Semantic Text Chunking**:
   - Use `LangChain`'s `RecursiveCharacterTextSplitter`.
   - Primary separators: `\n\n`, `\n`, `. `, ` `, `""`.
   - Default configuration: `chunk_size = 1000` characters, `chunk_overlap = 200` characters.
5. **Metadata Enrichment**:
   - Each chunk is enriched with:
     - `chunk_id` (UUID4)
     - `doc_id` (Document UUID)
     - `filename` (Original file name)
     - `page_number` (Specific page where chunk originated)
     - `chunk_index` (Sequential order within page/document)
6. **Vector Embedding & ChromaDB Indexing**:
   - Generate dense vector embeddings using `SentenceTransformers` (`all-MiniLM-L6-v2` or `bge-small-en-v1.5`, 384 dimensions).
   - Store vectors and metadata into an embedded `ChromaDB` collection.

---

### B. RAG & Retrieval Engine
1. **Query Embedding**:
   - Embed user questions using the identical `SentenceTransformers` model.
2. **Similarity Search**:
   - Perform Cosine Similarity / Distance search in ChromaDB.
   - Retrieve Top-$K$ relevant chunks (default: $K = 4$).
3. **Relevance Thresholding**:
   - Filter out chunks below a defined similarity cutoff to reject irrelevant documents.
4. **Context Construction & Prompt Engineering**:
   - Format retrieved chunks into a structured context block with page markers.
   - System Prompt enforces strict grounding:
     > *"You are an assistant answering questions strictly based on the provided context. If the answer cannot be determined from the context, state 'I am unable to find the answer in the provided documents.' Do not invent information."*
5. **LLM Provider Abstraction**:
   - Abstract adapter pattern for:
     - OpenAI (`gpt-4o-mini`, `gpt-3.5-turbo`)
     - Ollama (Local open-weight models like `llama3`, `mistral`)
     - Groq (`llama-3.1-8b-instant`)
     - Anthropic (`claude-3-haiku`)
   - Async streaming generation (`AsyncGenerator[str, None]`).
6. **Citation Resolver**:
   - Map LLM answer context back to the precise `filename` and `page_number` chunks used.

---

### C. Frontend User Experience (React + Tailwind CSS)
1. **Document Management Panel**:
   - Drag-and-drop file upload dropzone.
   - Upload progress bar and real-time processing indicator.
   - Document table/list displaying: Name, Page Count, Chunk Count, Status Badge, Delete Button.
2. **Conversational Chat Interface**:
   - Message history thread (User prompt, AI assistant response).
   - Token streaming animation for real-time text delivery.
   - Markdown formatting (bold, code blocks, bullet points) via `react-markdown`.
3. **Source Citation UI**:
   - Collapsible citation cards below AI responses.
   - Displays: Document Name, Page Number, Relevant Snippet Preview, Similarity Score badge.
4. **UX States**:
   - Loading skeletons during retrieval & processing.
   - Error banners for API failures or invalid files.
   - Empty state guidance for first-time users.

---

## 4. Non-Functional Requirements (NFRs)

- **Performance**:
  - PDF Ingestion: $\le 5$ seconds for a 20-page document.
  - Vector Retrieval: $\le 200$ ms for Top-4 chunks in ChromaDB.
  - Time To First Token (TTFT): $\le 1$ second for streaming responses.
- **Accuracy & Groundedness**:
  - $0\%$ tolerance for hallucinated sources; every citation must correspond to an actual retrieved chunk.
- **Security & Privacy**:
  - Secrets stored exclusively in `.env` (never committed to Git).
  - Strict input sanitization on uploaded files and query inputs.
  - CORS restricted to configured origins.
- **Maintainability & Code Quality**:
  - Clean Layered Architecture (Router $\rightarrow$ Service $\rightarrow$ Adapter / Repository).
  - Typing with Python `Pydantic` v2 and TypeScript/JSDoc types in React.
  - Clean modular styling with Tailwind CSS.

---

## 5. Development Phases

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Architecture & Technical Specs (CURRENT)                        │
│ └─ Technical breakdown, folder structure, API schemas, design docs       │
├─────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Backend Foundation & Ingestion Engine                          │
│ └─ FastAPI setup, PyMuPDF parser, Text cleaning, Chunking, Embeddings    │
│ └─ ChromaDB vector store wrapper & document deletion lifecycle           │
├─────────────────────────────────────────────────────────────────────────┤
│ Phase 3: RAG Retrieval & Provider-Agnostic LLM Layer                    │
│ └─ Vector search, prompt builder, LLM provider abstraction, SSE streaming │
├─────────────────────────────────────────────────────────────────────────┤
│ Phase 4: Frontend Application (Vite + React + Tailwind)                  │
│ └─ Document Uploader, Document List, Streaming Chat UI, Citation Drawer  │
├─────────────────────────────────────────────────────────────────────────┤
│ Phase 5: Automated Testing & RAG Evaluation                             │
│ └─ Pytest unit & API integration tests, Vitest UI component tests        │
├─────────────────────────────────────────────────────────────────────────┤
│ Phase 6: Containerization & Documentation                               │
│ └─ Multi-stage Dockerfiles, Docker Compose setup, comprehensive README   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Testing Strategy

### Backend (Pytest)
- **Unit Tests**:
  - `test_document_service`: Validate PyMuPDF text extraction accuracy across single and multi-page PDFs.
  - `test_text_processor`: Validate `RecursiveCharacterTextSplitter` chunk sizes, overlaps, and page metadata preservation.
  - `test_embedding_service`: Verify vector generation dimensions (384-dim) and normalization.
  - `test_llm_service`: Test LLM factory adapter pattern with mock responses.
- **Integration Tests**:
  - `test_chroma_service`: Verify add, query, and delete operations on ChromaDB test collection.
  - `test_api_endpoints`: Use `httpx.AsyncClient` to test `/api/v1/documents/upload`, `/api/v1/documents`, `/api/v1/chat/stream`, `/api/v1/health`.

### Frontend (Vitest + React Testing Library)
- **Component Tests**:
  - `FileUploader.test.jsx`: Verify drag-and-drop, invalid file rejection (.txt, .exe), max size warning.
  - `DocumentList.test.jsx`: Verify rendering of document items, delete trigger, loading/empty states.
  - `ChatInterface.test.jsx`: Verify message rendering, user prompt submission, citation toggles.

---

## 7. Deployment Strategy

- **Containerization (Docker)**:
  - **Backend Container**: Python 3.11 slim image running FastAPI with Uvicorn worker. Embeds ChromaDB persistent storage in a dedicated volume.
  - **Frontend Container**: Node build step generating static assets served via Nginx reverse proxy.
- **Docker Compose Orchestration**:
  - Single command startup: `docker compose up --build`.
  - Named volumes for ChromaDB persistence (`chroma_data`) and HuggingFace cache (`hf_cache`).
  - Bridge network connecting frontend and backend services cleanly.

---

## 8. Definition of Done (DoD)

- [ ] End-to-end user flow working: PDF Upload $\rightarrow$ Processing $\rightarrow$ Vector Store $\rightarrow$ Streaming Q&A $\rightarrow$ Citation Display.
- [ ] Strict Groundedness: System gracefully declines questions outside document context without hallucinating.
- [ ] Document lifecycle: Uploaded document vectors can be deleted, preventing stale answers.
- [ ] Automated Test Suite: Pytest backend coverage $\ge 80\%$, Vitest frontend tests pass clean.
- [ ] Code Quality: Fully documented, standard formatting (`black` / `ruff`, `eslint` / `prettier`), zero hardcoded credentials.
- [ ] Containerized Delivery: `docker compose up` starts entire stack without manual dependencies.
- [ ] Complete Documentation: `PROJECT_PLAN.md`, `ARCHITECTURE.md`, and top-level `README.md` present.
