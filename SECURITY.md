# Security & Production Authorization Architecture

This document details the security posture, prompt injection defenses, file upload boundaries, and production authentication/authorization requirements for the **RAG Document Q&A** platform.

---

## 1. Security Architecture & Current Hardening Controls

| Security Category | Implementation Controls | Configuration Boundary |
|---|---|---|
| **File Upload Validation** | Strict `.pdf` extension check, `%PDF-` magic header verification, PyMuPDF structure check, 0-byte detection. | `MAX_UPLOAD_SIZE_MB = 25` |
| **Path Traversal Protection** | Basename extraction (`os.path.basename`) and null byte / non-printable byte stripping via regex `[\x00-\x1f\x7f-\x9f]`. | Enforced on all upload routes |
| **Resource Exhaustion** | Strict max page count limit prevents PDF decompression bombs and high-memory rendering. | `MAX_DOCUMENT_PAGES = 500` |
| **Prompt Injection Defense** | Retrieved context chunks wrapped in `--- UNTRUSTED RETRIEVED DOCUMENT CONTEXT START ---` tags with strict system prompt instructions. | `RAG_SYSTEM_PROMPT` in `llm_service.py` |
| **Secret & API Key Exposure** | Sensitive LLM keys (`OPENAI_API_KEY`, `GROQ_API_KEY`) masked via `_mask_key()` in logs and representations. Never passed to frontend client. | `env_file = ".env"` |
| **XSS & Code Execution** | Frontend answer rendering uses `ReactMarkdown` without `dangerouslySetInnerHTML` or raw script execution. | React Virtual DOM sanitization |
| **Error Leakage Prevention** | Global exception handlers catch unhandled `Exception` instances and return sanitized HTTP 500 responses without tracebacks or file paths. | `main.py` exception handlers |

---

## 2. Production Authentication & Authorization Blueprint

To deploy this RAG engine into enterprise multi-tenant or team environments, the following production authentication and role-based access controls (RBAC) must be added:

### A. Authentication Architecture
- **JWT / OAuth2 Bearer Tokens**:
  - Integrate an Identity Provider (Auth0, Okta, Keycloak, Firebase, or FastAPI `OAuth2PasswordBearer`).
  - Pass JWT token in `Authorization: Bearer <token>` HTTP header on all API endpoints.
  - Verify token signatures using standard RS256/ES256 public keys.

### B. Multi-Tenant Document & Vector Storage Isolation
- **User / Tenant Metadata Tagging**:
  - Tag every document metadata record in `documents.json` with `user_id` and `tenant_id`.
  - Tag every ChromaDB vector chunk metadata with `user_id` and `tenant_id`:
    ```python
    metadatas.append({
        "document_id": str(chunk["document_id"]),
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        ...
    })
    ```
- **Scoped Vector Retrieval Filters**:
  - Enforce `where={"tenant_id": current_user.tenant_id}` on all vector similarity searches in `VectorService.similarity_search()`.
  - Prevents cross-tenant document data leakage during vector query retrieval.

### C. Rate Limiting & Abuse Prevention
- **API Rate Limiting**:
  - Add `slowapi` or Redis-backed sliding window rate limiter (e.g. max 10 document uploads/min and 60 chat queries/min per user).
- **Request Size Limiting**:
  - Configure reverse proxy (Nginx / Cloudflare / AWS ALB) with `client_max_body_size 25M;`.

---

## 3. Prompt Injection Verification Test

Run the dedicated security test suite to verify prompt injection defenses:
```bash
pytest app/tests/test_security.py -v
```
