import React, { useState } from 'react';
import { FileText, Layers, Trash2, CheckCircle2, Filter } from 'lucide-react';

export function DocumentItem({ document, isSelected, onSelect, onDelete }) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete "${document.filename}" and purge all its vectors from ChromaDB?`)) {
      setIsDeleting(true);
      try {
        await onDelete(document.document_id);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  return (
    <div
      onClick={() => onSelect(document.document_id)}
      className={`group relative p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
        isSelected
          ? 'bg-indigo-500/10 border-indigo-500/50 shadow-md shadow-indigo-500/10'
          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
      } ${isDeleting ? 'opacity-50 pointer-events-none' : ''}`}
    >
      <div className="flex items-center space-x-3 min-w-0">
        <div
          className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
            isSelected
              ? 'bg-indigo-500 text-white shadow-sm'
              : 'bg-slate-800 text-slate-400 group-hover:text-indigo-400'
          }`}
        >
          <FileText className="w-4 h-4" />
        </div>

        <div className="min-w-0">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-medium text-slate-200 truncate" title={document.filename}>
              {document.filename}
            </h4>
            {isSelected && (
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shrink-0">
                <Filter className="w-2.5 h-2.5" /> Scope Filter Active
              </span>
            )}
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
            <span className="flex items-center space-x-1">
              <FileText className="w-3 h-3 text-slate-500" />
              <span>{document.page_count} {document.page_count === 1 ? 'page' : 'pages'}</span>
            </span>
            <span>•</span>
            <span className="flex items-center space-x-1">
              <Layers className="w-3 h-3 text-slate-500" />
              <span>{document.chunk_count} chunks</span>
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2 shrink-0">
        <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-2.5 h-2.5" /> Indexed
        </span>

        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          title="Delete document and purge vectors"
          aria-label={`Delete ${document.filename}`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
