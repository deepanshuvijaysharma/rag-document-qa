import React from 'react';
import { UploadCloud, MessageSquareText } from 'lucide-react';

export function EmptyState({ type = 'documents', title, description, action }) {
  const isDocuments = type === 'documents';
  const Icon = isDocuments ? UploadCloud : MessageSquareText;

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 my-4">
      <div className="w-12 h-12 rounded-2xl bg-slate-800/80 flex items-center justify-center text-indigo-400 mb-3 border border-slate-700/50 shadow-inner">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-200">
        {title || (isDocuments ? 'No Documents Uploaded' : 'Start a Conversation')}
      </h3>
      <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4 leading-relaxed">
        {description || (
          isDocuments
            ? 'Upload PDF documents to build your vector knowledge base for grounded Q&A.'
            : 'Ask any question based on your uploaded PDF documents to receive answers with source page citations.'
        )}
      </p>
      {action}
    </div>
  );
}
