import React from 'react';
import { FileText, Bookmark, Sparkles } from 'lucide-react';

export function SourceCard({ source }) {
  const matchPct = Math.round((source.relevance_score || 0) * 100);

  return (
    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all text-xs space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2 truncate min-w-0">
          <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span className="font-semibold text-slate-200 truncate" title={source.filename}>
            {source.filename}
          </span>
        </div>

        <span className="inline-flex items-center gap-1 font-semibold text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 shrink-0">
          <Bookmark className="w-2.5 h-2.5" /> Page {source.page_number}
        </span>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
        <span className="font-mono text-[10px] text-slate-500 truncate max-w-[140px]" title={source.chunk_id}>
          ID: {source.chunk_id.substring(0, 14)}...
        </span>
        <span className="flex items-center space-x-1 text-emerald-400 font-medium">
          <Sparkles className="w-2.5 h-2.5" />
          <span>{matchPct}% similarity</span>
        </span>
      </div>
    </div>
  );
}
