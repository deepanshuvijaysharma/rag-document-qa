import React, { useState } from 'react';
import { User, Bot, ChevronDown, ChevronUp, BookOpen, AlertTriangle } from 'lucide-react';
import { SourceCard } from './SourceCard';

export function ChatMessage({ message }) {
  const [showSources, setShowSources] = useState(true);
  const isUser = message.sender === 'user';
  const hasSources = message.sources && message.sources.length > 0;
  const isFallback = message.text === "I am unable to find the answer in the uploaded documents.";

  if (isUser) {
    return (
      <div className="flex items-start justify-end space-x-3 my-4">
        <div className="max-w-2xl bg-indigo-600 text-white p-4 rounded-2xl rounded-tr-none shadow-md shadow-indigo-600/10">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-white shrink-0 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-3 my-4">
      <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-purple-600/20">
        <Bot className="w-4 h-4" />
      </div>

      <div className="max-w-3xl flex-1 bg-slate-900 border border-slate-800 p-5 rounded-2xl rounded-tl-none space-y-4 shadow-sm">
        {isFallback ? (
          <div className="flex items-start space-x-2 text-amber-300 bg-amber-500/10 p-3 rounded-xl border border-amber-500/20 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{message.text}</p>
          </div>
        ) : (
          <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
            {message.text}
          </div>
        )}

        {hasSources && (
          <div className="pt-3 border-t border-slate-800/80 space-y-3">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center justify-between w-full text-xs font-semibold text-slate-400 hover:text-indigo-400 transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                Retrieved Context Sources ({message.sources.length})
              </span>
              {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showSources && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 animate-in fade-in duration-150">
                {message.sources.map((src, idx) => (
                  <SourceCard key={src.chunk_id || idx} source={src} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
