import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import { LoadingIndicator } from '../common/LoadingIndicator';

export function FileUpload({ onUpload, isUploading }) {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const inputRef = useRef(null);

  const validateAndUpload = (file) => {
    setValidationError(null);

    if (!file) return;

    // Check extension
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setValidationError('Only PDF files (.pdf) are supported.');
      return;
    }

    // Check size limit (25 MB)
    const maxBytes = 25 * 1024 * 1024;
    if (file.size > maxBytes) {
      setValidationError('File size exceeds the 25 MB maximum limit.');
      return;
    }

    onUpload(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndUpload(e.target.files[0]);
    }
  };

  return (
    <div className="w-full space-y-2">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer select-none ${
          dragActive
            ? 'border-indigo-500 bg-indigo-500/10 scale-[0.99]'
            : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-800/40'
        } ${isUploading ? 'opacity-70 pointer-events-none' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          className="hidden"
          disabled={isUploading}
          id="pdf-upload-input"
        />

        {isUploading ? (
          <LoadingIndicator label="Extracting text, chunking & indexing vectors into ChromaDB..." />
        ) : (
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">
                Click or drag PDF document here
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                PDF up to 25 MB • Page numbers preserved for citations
              </p>
            </div>
          </div>
        )}
      </div>

      {validationError && (
        <div className="flex items-center space-x-2 text-xs text-rose-400 bg-rose-500/10 px-3 py-2 rounded-lg border border-rose-500/20">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
}
