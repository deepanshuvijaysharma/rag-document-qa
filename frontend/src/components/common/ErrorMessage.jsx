import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start justify-between gap-3 text-rose-300 animate-in fade-in duration-200">
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-rose-200">Processing Error</h4>
          <p className="text-xs text-rose-300/90 mt-0.5 leading-relaxed">{message}</p>
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-rose-400 hover:text-rose-200 p-1 rounded-lg hover:bg-rose-500/20 transition-colors"
          title="Dismiss Error"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
