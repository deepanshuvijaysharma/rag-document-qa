# Project Engineering Rules: RAG Document Q&A

This document establishes the mandatory engineering principles, code quality guidelines, and workflow standards for all AI agents and developers working on the **RAG Document Q&A** project.

---

## 1. Core Engineering Principles

### Code Understanding & Stability
1. **Understand Before Modifying**: Always inspect existing files, dependencies, and execution flows before attempting edits or refactoring.
2. **Preserve Working Functionality**: Never overwrite or break working implementations unnecessarily.
3. **Keep Unrelated Files Untouched**: Do not modify files outside the immediate scope of the assigned task.
4. **Step-by-Step Phasing**: Do not jump ahead to future phases unless explicitly instructed by the user.

### Security & Secret Management
5. **Never Hardcode Secrets**: Under no circumstances should API keys, database credentials, or secret tokens be hardcoded into source files.
6. **No Keys in Frontend**: Never expose API keys or backend credentials in frontend client code or browser-accessible assets.
7. **Environment Variable Configuration**: Always read configuration values and API keys from environment variables (`.env` via Pydantic `BaseSettings`).
8. **Sanitize Logs**: Never log API keys, bearer tokens, or user secrets in application logs or standard output.

### RAG Integrity & Groundedness
9. **Single Source of Truth**: Uploaded documents are the sole source of truth for all generated answers.
10. **Context-Constrained LLM Responses**: The LLM must answer questions strictly using the retrieved document context. It must never rely on pre-trained parametric memory to fabricate answers.
11. **Graceful Insufficient Context Fallback**: If retrieved context lacks the necessary information to answer a question, the system must clearly state that the answer could not be found in the uploaded documents.
12. **No Fake Functionality or Mocks**: Never create fake RAG retrievals, hardcoded AI answers, or dummy backend endpoints that pretend to work.

### Data & Metadata Integrity
13. **Preserve Document Metadata**: Always retain document identifiers (`doc_id`), original filenames, creation timestamps, and chunk indices throughout the pipeline.
14. **Preserve Page Numbers**: Preserve and propagate exact 1-indexed page numbers from PDF parsing through text splitting, vector storage, retrieval, and citation UI rendering.

### Architecture & Code Structure
15. **Clear Separation of Concerns**: Maintain strict boundaries between API routes (`api/`), business services (`services/`), data storage (`db/`), and schemas (`schemas/`).
16. **Keep Business Logic Out of Routes**: API handlers must only perform validation, call underlying service methods, and format HTTP responses.
17. **Separate Frontend & Backend**: Maintain a strict decoupled boundary between React client state/UI logic and FastAPI server infrastructure.
18. **Small Reusable Functions**: Write modular, single-responsibility helper functions instead of monolithic blocks of code.
19. **Avoid Unnecessary Dependencies**: Use native tools and standard libraries where appropriate; avoid pulling in bloated or redundant third-party libraries.
20. **Use Current Stable APIs**: Stick to verified, current stable APIs for libraries (e.g., PyMuPDF, ChromaDB, FastAPI, LangChain). Verify signatures before implementation.
21. **Portfolio-Quality Code**: Write clean, readable code optimized for maintainability, documentation, and interview explainability.

### Type Safety & Validation
22. **Python Type Hints**: Use explicit type annotations across all Python functions, parameters, and return signatures.
23. **Pydantic Data Schemas**: Validate all incoming API request payloads and outgoing response models using Pydantic v2 schemas.
24. **File Upload Validation**: Validate file extensions (`.pdf`), MIME types, and magic headers (`%PDF-`) prior to processing.
25. **Safe File Path Handling**: Protect against path traversal vulnerabilities by sanitizing filenames and isolating temp storage paths.

### Error Handling & Testing
26. **Explicit Error Handling**: Handle expected exceptions gracefully with custom domain exceptions and structured HTTP status codes.
27. **Never Swallow Exceptions**: Do not use empty `except:` blocks, silent fallback returns, or unhandled promise rejections.
28. **Comprehensive Automated Testing**: Write unit and integration tests (Pytest for backend, Vitest for frontend) for critical pipeline stages.
29. **Test After Changes**: Execute relevant test suites after making meaningful architectural or functional updates.
30. **Runtime Verification**: Run the application locally and empirically verify behavior before declaring a task complete.
31. **No False Claims**: Never claim a feature is complete or fixed without running direct verification commands.

### Documentation & Decisions
32. **Synchronize Documentation**: Update `PROJECT_PLAN.md`, `ARCHITECTURE.md`, and `README.md` whenever architectural patterns or API contracts change.
33. **Explain Technical Rationale**: Document non-obvious engineering decisions and trade-offs using clear code comments or architectural documentation.

---

## 2. Agent Workflow

To ensure systematic and predictable implementation, all agents working on this codebase must follow the standard 5-step engineering workflow:

```
┌───────────┐     ┌─────────────┐     ┌──────────┐     ┌───────────┐     ┌───────────┐
│   PLAN    │ ──► │  IMPLEMENT  │ ──► │   TEST   │ ──► │  VERIFY   │ ──► │  REPORT   │
└───────────┘     └─────────────┘     └──────────┘     └───────────┘     └───────────┘
```

### Mandatory Execution Steps

1. **PLAN**:
   - Inspect existing files, module schemas, and tests before writing code.
   - Outline the intended changes, impact on other components, and verification steps.
2. **IMPLEMENT**:
   - Write clean, modular, typed code following the project engineering principles.
   - Maintain separation between routes, services, schemas, and components.
3. **TEST**:
   - Run automated unit and integration tests (e.g., `pytest`, `vitest`).
   - Add new test cases covering new features or edge cases.
4. **VERIFY**:
   - Empirically verify application behavior via test outputs or runtime server logs.
   - Ensure zero lint errors, missing imports, or unhandled tracebacks.
5. **REPORT**:
   - Summarize what was implemented, key architectural decisions, test results, and next steps for the user.

### Subsystem Change Protocol
Before modifying a major subsystem (e.g., Document Ingestion, Embedding Engine, RAG Service, LLM Factory, Chat Interface):
1. **Inspect** existing subsystem files and caller locations.
2. **Explain** intended changes and potential side effects to the user or context.
3. **Implement** changes incrementally without breaking existing features.
4. **Test** the affected subsystem end-to-end.
5. **Report** precise verification outcomes.
