import React from 'react';
import { FileText, Cpu, ShieldCheck } from 'lucide-react';

export function Header({ activeDocCount = 0 }) {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              RAG Document Q&A
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Grounded GenAI
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Retrieval-Augmented Generation with strict page-level citations
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs text-slate-300 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/50">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span>Embedding: <strong className="text-indigo-300">all-MiniLM-L6-v2</strong></span>
          </div>
          <div className="flex items-center space-x-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Index Active ({activeDocCount} docs)</span>
          </div>
        </div>
      </div>
    </header>
  );
}
