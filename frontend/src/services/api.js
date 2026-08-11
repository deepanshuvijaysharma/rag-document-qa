/**
 * Backend API Client Layer for RAG Document Q&A Application.
 * Communicates with FastAPI backend endpoints.
 */

const API_BASE_URL = '/api';

/**
 * Helper to handle HTTP response errors cleanly.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `HTTP error! status: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Fallback if response is not JSON
    }
    throw new Error(errorMessage);
  }
  return await response.json();
}

/**
 * Upload a PDF document file to the backend ingestion pipeline.
 * @param {File} file - PDF File object to upload
 * @returns {Promise<Object>} DocumentUploadResponse { document_id, filename, file_size, page_count, chunk_count, status }
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  return await handleResponse(response);
}

/**
 * Fetch summary list of all active ingested PDF documents.
 * @returns {Promise<Object>} DocumentListResponse { documents: [...], total_count }
 */
export async function getDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  return await handleResponse(response);
}

/**
 * Fetch single document metadata details including pages and chunks.
 * @param {string} documentId - Document UUID
 * @returns {Promise<Object>} DocumentUploadResponse
 */
export async function getDocumentDetails(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  return await handleResponse(response);
}

/**
 * Delete a document metadata record and purge its vectors from ChromaDB.
 * @param {string} documentId - Document UUID to delete
 * @returns {Promise<Object>} { document_id, filename, status, vectors_purged }
 */
export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
    headers: {
      'Accept': 'application/json',
    },
  });

  return await handleResponse(response);
}

/**
 * Send a natural language message to the grounded RAG QA pipeline.
 * @param {string} message - User question text
 * @param {string|null} documentId - Optional document ID filter
 * @param {string|null} conversationId - Optional session ID
 * @returns {Promise<Object>} ChatResponse { conversation_id, answer, sources: [...] }
 */
export async function sendChatMessage(message, documentId = null, conversationId = null) {
  const payload = {
    message,
    document_id: documentId || null,
    conversation_id: conversationId || null,
  };

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return await handleResponse(response);
}
