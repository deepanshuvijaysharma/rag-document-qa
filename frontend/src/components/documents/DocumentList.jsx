import React from 'react';
import { DocumentItem } from './DocumentItem';
import { EmptyState } from '../common/EmptyState';
import { Layers, Globe } from 'lucide-react';

export function DocumentList({
  documents = [],
  selectedDocId,
  onSelectDoc,
  onDeleteDoc,
  isLoading
}) {
  if (!isLoading && documents.length === 0) {
    return <EmptyState type="documents" />;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          Active Vector Knowledge Base ({documents.length})
        </h3>

        {selectedDocId && (
          <button
            onClick={() => onSelectDoc(null)}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 hover:underline"
          >
            <Globe className="w-3 h-3" /> Clear Scope (Search All)
          </button>
        )}
      </div>

      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {documents.map((doc) => (
          <DocumentItem
            key={doc.document_id}
            document={doc}
            isSelected={selectedDocId === doc.document_id}
            onSelect={(id) => onSelectDoc(selectedDocId === id ? null : id)}
            onDelete={onDeleteDoc}
          />
        ))}
      </div>
    </div>
  );
}
