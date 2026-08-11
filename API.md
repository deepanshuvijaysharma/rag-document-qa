# RAG Document Q&A - API Endpoint Documentation

This document provides full OpenAPI technical specifications for all REST and Server-Sent Events (SSE) streaming endpoints provided by the **RAG Document Q&A** backend API.

---

## Base URLs & Interactive OpenAPI Docs

- **Base Endpoint**: `http://127.0.0.1:8000/api/v1` (Alias: `http://127.0.0.1:8000/api`)
- **Swagger UI Interactive Docs**: `http://127.0.0.1:8000/api/v1/docs`
- **ReDoc Technical Docs**: `http://127.0.0.1:8000/api/v1/redoc`

---

## 1. System Health Check

### `GET /health`
Returns system operational status.

- **Status Code**: `200 OK`
- **Response**:
```json
{
  "status": "ok"
}
```

---

## 2. Document Ingestion & Management

### `POST /api/documents/upload`
Uploads a PDF document, validates file structure, extracts page text, generates semantic chunks, embeds vector representations via SentenceTransformers, indexes vectors into ChromaDB, and persists document metadata.

- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `file` (File, required): PDF document file (`.pdf`, max 25MB, max 500 pages).
- **Status Code**: `200 OK`
- **Response**:
```json
{
  "document_id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
  "filename": "sample_employee_handbook.pdf",
  "file_size": 2707,
  "page_count": 2,
  "chunk_count": 2,
  "status": "processed",
  "pages": [
    {
      "page_number": 1,
      "text": "Employee Handbook Section 1..."
    }
  ],
  "chunks": [
    {
      "chunk_id": "chunk-866504a7-88d4-42b7-bd20-7fbe8b556ec0-0",
      "document_id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
      "source_filename": "sample_employee_handbook.pdf",
      "page_number": 1,
      "chunk_index": 0,
      "text": "Employee Handbook Section 1..."
    }
  ]
}
```
- **Error Responses**:
  - `400 Bad Request`: Invalid file extension, non-PDF content, file size exceeding 25MB limit.
  - `422 Unprocessable Content`: Corrupted PDF bytes, encrypted PDF, zero extractable text layer.

---

### `GET /api/documents`
Retrieves a list of all active uploaded PDF documents.

- **Status Code**: `200 OK`
- **Response**:
```json
{
  "total_count": 1,
  "documents": [
    {
      "id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
      "document_id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
      "filename": "sample_employee_handbook.pdf",
      "file_size": 2707,
      "page_count": 2,
      "chunk_count": 2,
      "upload_timestamp": "2026-08-11T16:50:03.123456",
      "status": "processed"
    }
  ]
}
```

---

### `GET /api/documents/{id}`
Retrieves detailed metadata, extracted pages, and text chunks for a specific document.

- **Status Code**: `200 OK`
- **Error Response**: `404 Not Found` if `id` does not exist in metadata store.

---

### `DELETE /api/documents/{id}`
Deletes a document metadata record and purges all associated vector embeddings from ChromaDB.

- **Status Code**: `200 OK`
- **Response**:
```json
{
  "document_id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
  "filename": "sample_employee_handbook.pdf",
  "status": "deleted",
  "vectors_purged": 2
}
```

---

## 3. Vector Retrieval Testing Endpoint

### `POST /api/retrieval/search`
Internal testing endpoint to execute query vector embedding and similarity search against ChromaDB without calling the LLM.

- **Content-Type**: `application/json`
- **Request Body**:
```json
{
  "query": "annual leave policy",
  "top_k": 4,
  "document_id": null
}
```
- **Response**:
```json
{
  "query": "annual leave policy",
  "total_results": 1,
  "results": [
    {
      "chunk_id": "chunk-866504a7-88d4-42b7-bd20-7fbe8b556ec0-0",
      "document_id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
      "filename": "sample_employee_handbook.pdf",
      "page_number": 1,
      "chunk_index": 0,
      "text": "Employee Handbook Section 1: Annual Leave...",
      "distance": 0.1579,
      "score": 0.8421
    }
  ]
}
```

---

## 4. Grounded RAG Chat & Q&A Endpoints

### `POST /api/chat` (Non-Streaming)
Executes complete grounded RAG Q&A pipeline: query validation $\rightarrow$ vector retrieval $\rightarrow$ relevance score thresholding ($\ge 0.35$) $\rightarrow$ context construction $\rightarrow$ LLM generation $\rightarrow$ citation extraction $\rightarrow$ session persistence.

- **Content-Type**: `application/json`
- **Request Body**:
```json
{
  "message": "What is the annual leave policy?",
  "document_id": null,
  "conversation_id": "session-123"
}
```
- **Response**:
```json
{
  "conversation_id": "session-123",
  "answer": "Full-time employees accrue 20 days of paid annual leave per calendar year.",
  "sources": [
    {
      "document_id": "866504a7-88d4-42b7-bd20-7fbe8b556ec0",
      "filename": "sample_employee_handbook.pdf",
      "page_number": 1,
      "chunk_id": "chunk-866504a7-88d4-42b7-bd20-7fbe8b556ec0-0",
      "relevance_score": 0.8421,
      "snippet": "Employee Handbook Section 1: Annual Leave & Paid Time Off Policy..."
    }
  ]
}
```

---

### `POST /api/chat/stream` (Server-Sent Events SSE)
Streams grounded RAG Q&A responses token-by-token using Server-Sent Events (`text/event-stream`).

- **Content-Type**: `application/json`
- **Request Body**:
```json
{
  "message": "What is the annual leave policy?",
  "document_id": null,
  "conversation_id": "stream-session-123"
}
```
- **Stream Protocol Event Flow**:
  1. `event: metadata`
     `data: {"conversation_id": "...", "sources": [...]}`
  2. `event: token`
     `data: {"token": "Full-time "}`
  3. `event: token`
     `data: {"token": "employees..."}`
  4. `event: done`
     `data: {"status": "complete"}`
