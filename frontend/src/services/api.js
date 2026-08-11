/**
 * Frontend REST API Client Service Layer.
 */

const API_BASE_URL = '/api';

/**
 * Upload a PDF document to the backend RAG ingestion pipeline.
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
  }

  return await response.json();
}

/**
 * Fetch list of all active uploaded PDF documents.
 */
export async function getDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch documents' }));
    throw new Error(errorData.detail || `HTTP error ${response.status}`);
  }

  return await response.json();
}

/**
 * Fetch detailed metadata and chunks for a specific document.
 */
export async function getDocumentDetails(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch document details' }));
    throw new Error(errorData.detail || `HTTP error ${response.status}`);
  }

  return await response.json();
}

/**
 * Delete a document and purge its vectors from ChromaDB.
 */
export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to delete document' }));
    throw new Error(errorData.detail || `HTTP error ${response.status}`);
  }

  return await response.json();
}

/**
 * Send natural language question to RAG Q&A engine (Non-Streaming).
 */
export async function sendChatMessage({ message, documentId, conversationId }) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      document_id: documentId || null,
      conversation_id: conversationId || null,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Chat query failed' }));
    throw new Error(errorData.detail || `Chat query failed with status ${response.status}`);
  }

  return await response.json();
}

/**
 * Stream natural language question to RAG Q&A engine (Server-Sent Events SSE).
 */
export async function sendStreamingChatMessage({
  message,
  documentId,
  conversationId,
  onMetadata,
  onToken,
  onSources,
  onError,
  onComplete,
}) {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      document_id: documentId || null,
      conversation_id: conversationId || null,
    }),
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => 'Server error');
    throw new Error(errText || `Server returned HTTP ${response.status}`);
  }

  if (!response.body) {
    throw new Error('ReadableStream not supported by browser environment.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split('\n\n');
      buffer = blocks.pop() || '';

      for (const block of blocks) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/^event:\s*(.+)$/m);
        const dataMatch = block.match(/^data:\s*(.+)$/m);

        if (eventMatch && dataMatch) {
          const eventName = eventMatch[1].trim();
          try {
            const payload = JSON.parse(dataMatch[1].trim());
            if (eventName === 'metadata') {
              if (onMetadata) onMetadata(payload);
              if (payload.sources && onSources) onSources(payload.sources);
            } else if (eventName === 'token') {
              if (onToken) onToken(payload.token);
            } else if (eventName === 'done') {
              if (onComplete) onComplete(payload);
            } else if (eventName === 'error') {
              if (onError) onError(new Error(payload.detail || 'Streaming error'));
            }
          } catch (err) {
            console.error('Failed parsing SSE payload:', err);
          }
        }
      }
    }

    if (buffer.trim()) {
      const eventMatch = buffer.match(/^event:\s*(.+)$/m);
      const dataMatch = buffer.match(/^data:\s*(.+)$/m);
      if (eventMatch && dataMatch) {
        const eventName = eventMatch[1].trim();
        try {
          const payload = JSON.parse(dataMatch[1].trim());
          if (eventName === 'token' && onToken) onToken(payload.token);
          if (eventName === 'metadata') {
            if (onMetadata) onMetadata(payload);
            if (payload.sources && onSources) onSources(payload.sources);
          }
        } catch (e) {
          /* ignore trailing partial */
        }
      }
    }

    if (onComplete) onComplete();
  } catch (err) {
    if (onError) onError(err);
    else throw err;
  }
}
