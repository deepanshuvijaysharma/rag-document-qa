import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingIndicator({ label = 'Processing...', inline = false }) {
  if (inline) {
    return (
      <div className="flex items-center space-x-2 text-xs text-indigo-400">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span>{label}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-6 space-y-3">
      <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
        <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
      </div>
      <p className="text-sm font-medium text-slate-300">{label}</p>
    </div>
  );
}
