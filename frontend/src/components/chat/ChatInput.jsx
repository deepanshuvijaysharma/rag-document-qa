import React, { useState } from 'react';
import { Send, Filter, Sparkles } from 'lucide-react';

export function ChatInput({ onSendMessage, isSubmitting, selectedDoc, hasDocuments }) {
  const [inputMessage, setInputMessage] = useState('');

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || isSubmitting || !hasDocuments) return;

    onSendMessage(inputMessage.trim());
    setInputMessage('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-2">
      {selectedDoc && (
        <div className="flex items-center justify-between text-xs text-indigo-300 bg-indigo-500/10 px-3 py-1.5 rounded-lg border border-indigo-500/20">
          <span className="flex items-center gap-1.5 truncate">
            <Filter className="w-3.5 h-3.5" /> Scoped to: <strong className="truncate">{selectedDoc.filename}</strong>
          </span>
          <span className="text-[10px] text-indigo-400/80">Only querying this document</span>
        </div>
      )}

      <div className="relative flex items-center bg-slate-900 border border-slate-800 rounded-2xl focus-within:border-indigo-500/60 focus-within:ring-1 focus-within:ring-indigo-500/30 transition-all p-1.5 shadow-lg">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            hasDocuments
              ? selectedDoc
                ? `Ask any question about "${selectedDoc.filename}"...`
                : 'Ask any question across all uploaded PDF documents...'
              : 'Upload at least one PDF document to start asking questions...'
          }
          disabled={isSubmitting || !hasDocuments}
          rows={1}
          className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 px-4 py-3 resize-none focus:outline-none disabled:opacity-50 min-h-[44px] max-h-32"
          id="chat-question-input"
        />

        <button
          type="submit"
          disabled={!inputMessage.trim() || isSubmitting || !hasDocuments}
          className="shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-40 disabled:pointer-events-none shadow-md shadow-indigo-500/20 mr-1"
          title="Send Question (Enter)"
          aria-label="Send Question"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-500 px-2">
        <span>Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">Enter</kbd> to send</span>
        <span className="flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-indigo-400" /> Grounded in vector store context
        </span>
      </div>
    </form>
  );
}
