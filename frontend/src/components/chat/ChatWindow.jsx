import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { EmptyState } from '../common/EmptyState';
import { LoadingIndicator } from '../common/LoadingIndicator';
import { MessageSquareText } from 'lucide-react';

export function ChatWindow({ messages = [], isLoading, hasDocuments }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950/40 rounded-2xl border border-slate-800/80 p-4 md:p-6 overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <MessageSquareText className="w-3.5 h-3.5 text-indigo-400" />
          Interactive RAG Q&A Session
        </h3>
        <span className="text-xs text-slate-500">
          {messages.length} {messages.length === 1 ? 'message' : 'messages'}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {messages.length === 0 ? (
          <EmptyState
            type="chat"
            description={
              hasDocuments
                ? 'Your documents are indexed! Ask any question below to retrieve grounded answers with source page numbers.'
                : 'Upload PDF documents in the left sidebar to enable vector retrieval Q&A.'
            }
          />
        ) : (
          messages.map((msg, idx) => (
            <ChatMessage key={msg.id || idx} message={msg} />
          ))
        )}

        {isLoading && (
          <div className="flex items-center justify-center p-4">
            <LoadingIndicator label="Embedding query, searching ChromaDB vectors & generating grounded answer..." />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
