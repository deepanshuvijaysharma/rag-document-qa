import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot, ChevronDown, ChevronUp, BookOpen, AlertTriangle, Copy, Check, Loader2 } from 'lucide-react';
import { SourceCard } from './SourceCard';

export function ChatMessage({ message }) {
  const [showSources, setShowSources] = useState(true);
  const [copied, setCopied] = useState(false);

  const isUser = message.sender === 'user';
  const hasSources = message.sources && message.sources.length > 0;
  const isFallback = message.text === "I am unable to find the answer in the uploaded documents.";
  const isStreaming = message.isStreaming;

  const handleCopy = () => {
    if (message.text) {
      navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isUser) {
    return (
      <div className="flex items-start justify-end space-x-3 my-4">
        <div className="max-w-2xl bg-indigo-600 text-white p-4 rounded-2xl rounded-tr-none shadow-md shadow-indigo-600/10">
          <p className="text-sm leading-relaxed whitespace-pre-wrap font-sans">{message.text}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-white shrink-0 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-3 my-5">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-500/20">
        <Bot className="w-4 h-4" />
      </div>

      <div className="max-w-3xl flex-1 bg-slate-900 border border-slate-800 p-5 rounded-2xl rounded-tl-none space-y-5 shadow-lg">
        {/* AI Answer Header & Copy Button */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
            <span>AI Answer</span>
            {isStreaming && (
              <span className="inline-flex items-center gap-1 text-[10px] text-indigo-300 font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                <Loader2 className="w-2.5 h-2.5 animate-spin" /> Streaming...
              </span>
            )}
          </span>

          <button
            onClick={handleCopy}
            disabled={isStreaming || !message.text}
            className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-slate-800 transition-colors disabled:opacity-40"
            title="Copy Answer"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>

        {/* Answer Text Section */}
        {isFallback ? (
          <div className="flex items-start space-x-2 text-amber-300 bg-amber-500/10 p-3.5 rounded-xl border border-amber-500/20 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{message.text}</p>
          </div>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed font-sans space-y-3 relative">
            {!message.text && isStreaming ? (
              <div className="flex items-center space-x-2 text-slate-400 text-sm italic py-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Searching document index and generating grounded answer...</span>
              </div>
            ) : (
              <>
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-2 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 pl-2 text-slate-300">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 pl-2 text-slate-300">{children}</ol>,
                    li: ({ children }) => <li className="text-slate-300">{children}</li>,
                    code: ({ inline, children }) =>
                      inline ? (
                        <code className="bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
                      ) : (
                        <pre className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs font-mono overflow-x-auto text-indigo-200 my-3">
                          <code>{children}</code>
                        </pre>
                      ),
                    strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                  }}
                >
                  {message.text}
                </ReactMarkdown>
                {isStreaming && (
                  <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse ml-1 align-middle" />
                )}
              </>
            )}
          </div>
        )}

        {/* Sources Citation Section */}
        {hasSources && (
          <div className="pt-4 border-t border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center justify-between w-full text-xs font-bold text-slate-300 hover:text-indigo-400 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" />
                  <span>Sources ({message.sources.length})</span>
                </span>
                {showSources ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>
            </div>

            {showSources && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1 animate-in fade-in duration-150">
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
