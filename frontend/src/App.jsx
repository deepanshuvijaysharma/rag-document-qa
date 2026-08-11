import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/common/Header';
import { FileUpload } from './components/documents/FileUpload';
import { DocumentList } from './components/documents/DocumentList';
import { ChatWindow } from './components/chat/ChatWindow';
import { ChatInput } from './components/chat/ChatInput';
import { ErrorMessage } from './components/common/ErrorMessage';

import * as api from './services/api';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);

  const [isUploading, setIsUploading] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isDocsLoading, setIsDocsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch active documents on initial mount
  const fetchDocuments = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      // Non-blocking error notice on initial fetch if backend is warming up
    } finally {
      setIsDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Handle PDF file upload
  const handleUpload = async (file) => {
    setIsUploading(true);
    setError(null);
    try {
      const result = await api.uploadDocument(file);
      await fetchDocuments();
      
      // Optionally auto-select the newly uploaded document
      if (result && result.document_id) {
        setSelectedDocId(result.document_id);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.message || 'Failed to upload and index PDF document.');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle document deletion
  const handleDeleteDocument = async (docId) => {
    setError(null);
    try {
      await api.deleteDocument(docId);
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
      await fetchDocuments();
    } catch (err) {
      console.error('Delete failed:', err);
      setError(err.message || 'Failed to delete document.');
    }
  };

  // Handle sending user question
  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    setError(null);
    const userMsgId = `user-${Date.now()}`;
    const newMessages = [
      ...messages,
      { id: userMsgId, sender: 'user', text: text.trim() }
    ];
    setMessages(newMessages);
    setIsChatLoading(true);

    try {
      const response = await api.sendChatMessage(
        text.trim(),
        selectedDocId,
        conversationId
      );

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const botMsgId = `bot-${Date.now()}`;
      setMessages([
        ...newMessages,
        {
          id: botMsgId,
          sender: 'bot',
          text: response.answer,
          sources: response.sources || []
        }
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message || 'Failed to generate answer from vector store.');
    } finally {
      setIsChatLoading(false);
    }
  };

  const selectedDocument = documents.find((d) => d.document_id === selectedDocId);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      <Header activeDocCount={documents.length} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left Column: Document Management Sidebar (4 cols on lg screens) */}
        <aside className="lg:col-span-4 flex flex-col space-y-6">
          <div className="glass-panel p-5 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold text-white tracking-wide uppercase flex items-center justify-between">
              <span>Document Ingestion</span>
              <span className="text-[10px] text-slate-400 font-normal">PDF Only</span>
            </h2>
            
            <FileUpload onUpload={handleUpload} isUploading={isUploading} />
          </div>

          <div className="glass-panel p-5 rounded-2xl flex-1 flex flex-col">
            <DocumentList
              documents={documents}
              selectedDocId={selectedDocId}
              onSelectDoc={setSelectedDocId}
              onDeleteDoc={handleDeleteDocument}
              isLoading={isDocsLoading}
            />
          </div>
        </aside>

        {/* Right Column: Chat Interface & Sources Area (8 cols on lg screens) */}
        <section className="lg:col-span-8 flex flex-col space-y-4 min-h-[600px] lg:min-h-0">
          <ErrorMessage message={error} onDismiss={() => setError(null)} />

          <ChatWindow
            messages={messages}
            isLoading={isChatLoading}
            hasDocuments={documents.length > 0}
          />

          <div className="glass-panel p-4 rounded-2xl">
            <ChatInput
              onSendMessage={handleSendMessage}
              isSubmitting={isChatLoading}
              selectedDoc={selectedDocument}
              hasDocuments={documents.length > 0}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
