import React, { useState } from 'react';
import { FileText, Bookmark, Sparkles, ChevronDown, ChevronUp, Eye } from 'lucide-react';

export function SourceCard({ source }) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Safe fallback metadata handling
  const filename = source?.filename || 'Document';
  const pageNumber = source?.page_number != null ? `Page ${source.page_number}` : 'Page N/A';
  const scoreVal = source?.relevance_score != null ? Number(source.relevance_score) : 0.0;
  const matchPct = Math.round(scoreVal * 100);
  const formattedScore = scoreVal.toFixed(2);
  const snippetText = source?.snippet || null;
  const chunkId = source?.chunk_id || 'N/A';

  return (
    <div
      onClick={() => setIsExpanded(!isExpanded)}
      className={`p-3.5 rounded-xl border transition-all cursor-pointer select-none space-y-2.5 ${
        isExpanded
          ? 'bg-slate-900 border-indigo-500/50 shadow-md shadow-indigo-500/10'
          : 'bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:bg-slate-800/60'
      }`}
    >
      {/* Top row: Filename + Page Number badge */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
            <FileText className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-xs text-slate-200 truncate" title={filename}>
            📄 {filename}
          </span>
        </div>

        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 shrink-0">
          <Bookmark className="w-2.5 h-2.5" /> {pageNumber}
        </span>
      </div>

      {/* Bottom row: Score & Expand Toggle */}
      <div className="flex items-center justify-between text-[11px] pt-2 border-t border-slate-800/80">
        <div className="flex items-center space-x-2 text-slate-400">
          <span className="flex items-center space-x-1 text-emerald-400 font-semibold">
            <Sparkles className="w-3 h-3" />
            <span>Relevance: {formattedScore} ({matchPct}%)</span>
          </span>
        </div>

        <div className="flex items-center space-x-1 text-slate-400 hover:text-indigo-300 font-medium text-[10px]">
          <Eye className="w-3 h-3 text-indigo-400" />
          <span>{isExpanded ? 'Hide Snippet' : 'View Snippet'}</span>
          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </div>
      </div>

      {/* Snippet Preview Drawer */}
      {isExpanded && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="mt-2 pt-2.5 border-t border-slate-800 text-xs text-slate-300 bg-slate-950/60 p-3 rounded-lg space-y-1.5 animate-in fade-in duration-150"
        >
          <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>CHUNK ID: {chunkId}</span>
            <span>{filename} • {pageNumber}</span>
          </div>

          {snippetText ? (
            <p className="italic text-slate-300/90 leading-relaxed border-l-2 border-indigo-500/60 pl-2.5 py-0.5">
              "{snippetText}"
            </p>
          ) : (
            <p className="text-slate-500 italic text-[11px]">
              No snippet text preview available for this vector chunk.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
