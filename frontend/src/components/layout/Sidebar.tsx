import React, { useState, useRef } from 'react';
import {
  Key,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  UploadCloud,
  FileCheck,
  Trash2,
  Cpu,
  Sliders,
  Compass,
  FileText,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { verifyLLMKey, uploadDocument, deleteDocument } from '../../services/api';
import { RAGMode } from '../../types';

export const Sidebar: React.FC = () => {
  const {
    sessionId,
    llmConfig,
    setLLMConfig,
    activeDocument,
    setActiveDocument,
    ragMode,
    setRAGMode,
    setActiveCitations
  } = useApp();

  const [showKey, setShowKey] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState<{ success?: boolean; message?: string } | null>(null);

  // Upload states
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleVerify = async () => {
    if (!llmConfig.apiKey.trim()) {
      setVerifyStatus({ success: false, message: 'Please enter an API Key' });
      return;
    }
    setIsVerifying(true);
    setVerifyStatus(null);
    try {
      const res = await verifyLLMKey(llmConfig.provider, llmConfig.apiKey, llmConfig.modelName);
      setVerifyStatus({ success: true, message: res.message || 'Connected successfully!' });
      setLLMConfig(prev => ({ ...prev, isVerified: true }));
    } catch (err: any) {
      setVerifyStatus({ success: false, message: err.message || 'Connection failed' });
      setLLMConfig(prev => ({ ...prev, isVerified: false }));
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF files are supported.');
      return;
    }
    if (file.size > 30 * 1024 * 1024) {
      setUploadError('File size exceeds 30MB limit.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    try {
      const doc = await uploadDocument(file, sessionId, llmConfig.provider, llmConfig.apiKey);
      setActiveDocument(doc);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to parse and index PDF.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async () => {
    if (!activeDocument) return;
    try {
      await deleteDocument(activeDocument.document_id, sessionId);
      setActiveDocument(null);
      setActiveCitations([]);
    } catch (err: any) {
      console.error('Failed to delete document', err);
    }
  };

  return (
    <aside className="w-80 h-[calc(100vh-4rem)] border-r border-purple-500/20 glass-panel overflow-y-auto p-5 flex flex-col space-y-6 flex-shrink-0 select-none">
      
      {/* 1. LLM Provider & Credentials */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2 text-xs font-semibold text-purple-300 uppercase tracking-wider">
          <Key className="w-3.5 h-3.5 text-purple-400" />
          <span>LLM Credentials</span>
        </div>

        <div className="space-y-2.5">
          {/* Provider selector */}
          <div className="grid grid-cols-2 gap-1.5 p-1 bg-black/40 rounded-lg border border-purple-500/20 text-xs">
            <button
              onClick={() => setLLMConfig(prev => ({ ...prev, provider: 'gemini', modelName: 'gemini-3.8-flash' }))}
              className={`py-1.5 rounded-md font-medium transition-all ${
                llmConfig.provider === 'gemini'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Google Gemini
            </button>
            <button
              onClick={() => setLLMConfig(prev => ({ ...prev, provider: 'openai', modelName: 'gpt-4o' }))}
              className={`py-1.5 rounded-md font-medium transition-all ${
                llmConfig.provider === 'openai'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              OpenAI
            </button>
          </div>

          {/* API Key Input */}
          <div className="relative">
            <input
              type={showKey ? 'text' : 'password'}
              value={llmConfig.apiKey}
              onChange={(e) => setLLMConfig(prev => ({ ...prev, apiKey: e.target.value, isVerified: false }))}
              placeholder={llmConfig.provider === 'gemini' ? 'Gemini API Key (AIzaSy...)' : 'OpenAI API Key (sk-...)'}
              className="w-full glass-input px-3 py-2 pr-9 text-xs rounded-lg text-slate-100 placeholder-slate-500 font-mono"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-2.5 top-2.5 text-slate-400 hover:text-purple-300 transition-colors"
            >
              {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Model ID Selector */}
          <div>
            <label className="text-[11px] text-slate-400 mb-1 block">Model Identifier</label>
            {llmConfig.provider === 'gemini' ? (
              <select
                value={llmConfig.modelName}
                onChange={(e) => setLLMConfig(prev => ({ ...prev, modelName: e.target.value }))}
                className="w-full glass-input px-3 py-1.5 text-xs rounded-lg text-slate-100 font-mono appearance-none bg-black/40 border border-purple-500/20"
              >
                <option value="gemini-2-flash">Gemini 2 Flash</option>
                <option value="gemini-2-flash-lite">Gemini 2 Flash Lite</option>
                <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</option>
                <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                <option value="gemini-3-flash">Gemini 3 Flash</option>
                <option value="gemini-3.1-pro">Gemini 3.1 Pro</option>
                <option value="gemini-3.1-flash-lite">Gemini 3.1 Flash Lite</option>
                <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
                <option value="gemini-3.5-flash-lite">Gemini 3.5 Flash Lite</option>
                <option value="gemini-3.6-flash">Gemini 3.6 Flash</option>
                <option value="gemini-3.7-flash">Gemini 3.7 Flash</option>
                <option value="gemini-3.8-flash">Gemini 3.8 Flash</option>
                <option value="gemma-4-25b">Gemma 4 25B</option>
                <option value="gemma-4-31b">Gemma 4 31B</option>
              </select>
            ) : (
              <select
                value={llmConfig.modelName}
                onChange={(e) => setLLMConfig(prev => ({ ...prev, modelName: e.target.value }))}
                className="w-full glass-input px-3 py-1.5 text-xs rounded-lg text-slate-100 font-mono appearance-none bg-black/40 border border-purple-500/20"
              >
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
              </select>
            )}
          </div>

          {/* Test Connection Button */}
          <button
            onClick={handleVerify}
            disabled={isVerifying}
            className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg bg-purple-900/40 hover:bg-purple-900/70 border border-purple-500/30 hover:border-purple-400 text-purple-200 text-xs font-medium transition-all duration-200 disabled:opacity-50"
          >
            {isVerifying ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />
            ) : (
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
            )}
            <span>{isVerifying ? 'Verifying...' : 'Test Connection'}</span>
          </button>

          {/* Verification Status */}
          {verifyStatus && (
            <div className={`flex items-start space-x-2 p-2 rounded-lg text-[11px] ${
              verifyStatus.success
                ? 'bg-emerald-950/40 border border-emerald-500/30 text-emerald-300'
                : 'bg-rose-950/40 border border-rose-500/30 text-rose-300'
            }`}>
              {verifyStatus.success ? (
                <CheckCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-emerald-400" />
              ) : (
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-rose-400" />
              )}
              <span className="break-all">{verifyStatus.message}</span>
            </div>
          )}
        </div>
      </div>

      <hr className="border-purple-500/15" />

      {/* 2. PDF Document Ingestion */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2 text-xs font-semibold text-purple-300 uppercase tracking-wider">
          <UploadCloud className="w-3.5 h-3.5 text-purple-400" />
          <span>Document Ingestion</span>
        </div>

        {activeDocument ? (
          /* Active Document Card */
          <div className="glass-card p-3 rounded-xl space-y-2.5 border-purple-500/30">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2 overflow-hidden">
                <FileCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="text-xs font-medium text-slate-100 truncate" title={activeDocument.filename}>
                  {activeDocument.filename}
                </span>
              </div>
              <button
                onClick={handleDeleteDocument}
                className="text-slate-400 hover:text-rose-400 p-1 transition-colors"
                title="Remove and delete document"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-purple-500/10 font-mono">
              <div>
                <span className="text-slate-400 block text-[10px]">Pages</span>
                <span className="text-purple-300 font-semibold">{activeDocument.page_count}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Chunks</span>
                <span className="text-purple-300 font-semibold">{activeDocument.chunk_count}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Characters</span>
                <span className="text-purple-300 font-semibold">{activeDocument.char_count.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Type</span>
                <span className="text-cyan-400 font-semibold">{activeDocument.is_scanned ? 'OCR Scanned' : 'Text PDF'}</span>
              </div>
            </div>
          </div>
        ) : (
          /* Upload Dropzone */
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragOver(false);
              if (e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files[0]);
              }
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 ${
              isDragOver
                ? 'border-purple-400 bg-purple-900/20'
                : 'border-purple-500/30 hover:border-purple-400/60 bg-black/20'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
            />
            {isUploading ? (
              <div className="space-y-2 py-2">
                <RefreshCw className="w-6 h-6 animate-spin text-purple-400 mx-auto" />
                <p className="text-xs text-purple-300 font-medium">Extracting & indexing...</p>
                <div className="w-full bg-purple-950/60 rounded-full h-1 overflow-hidden">
                  <div className="bg-purple-500 h-full w-2/3 animate-pulse" />
                </div>
              </div>
            ) : (
              <div className="space-y-1.5 py-1">
                <UploadCloud className="w-6 h-6 text-purple-400 mx-auto" />
                <p className="text-xs font-medium text-slate-200">
                  Drop PDF or <span className="text-purple-400 underline">Browse</span>
                </p>
                <p className="text-[10px] text-slate-500 font-mono">Max size: 30 MB</p>
              </div>
            )}
          </div>
        )}

        {uploadError && (
          <p className="text-[11px] text-rose-400 px-1">{uploadError}</p>
        )}
      </div>

      <hr className="border-purple-500/15" />

      {/* 3. RAG Execution Routing Mode */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2 text-xs font-semibold text-purple-300 uppercase tracking-wider">
          <Compass className="w-3.5 h-3.5 text-purple-400" />
          <span>RAG Routing Mode</span>
        </div>

        <div className="space-y-1.5">
          {[
            {
              id: 'auto' as RAGMode,
              title: 'Auto Router',
              desc: 'Intelligently routes between PDF evidence, general AI, and real-time tools.',
              icon: Sparkles
            },
            {
              id: 'document_only' as RAGMode,
              title: 'Document Only',
              desc: 'Strict ground truth: answers solely from PDF passages with citations.',
              icon: FileText
            },
            {
              id: 'general_ai' as RAGMode,
              title: 'General AI',
              desc: 'Bypasses PDF retrieval; answers using standard LLM intelligence and tools.',
              icon: Sliders
            }
          ].map((mode) => {
            const Icon = mode.icon;
            const isSelected = ragMode === mode.id;
            return (
              <button
                key={mode.id}
                onClick={() => setRAGMode(mode.id)}
                className={`w-full text-left p-2.5 rounded-xl border transition-all duration-150 ${
                  isSelected
                    ? 'bg-purple-900/40 border-purple-500/60 shadow-glass'
                    : 'bg-black/20 border-purple-500/15 hover:border-purple-500/30'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-purple-300' : 'text-slate-400'}`} />
                  <span className={`text-xs font-medium ${isSelected ? 'text-purple-200' : 'text-slate-300'}`}>
                    {mode.title}
                  </span>
                  {isSelected && (
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 ml-auto" />
                  )}
                </div>
                <p className="text-[10px] text-slate-400 mt-1 pl-5.5 leading-relaxed">
                  {mode.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>

    </aside>
  );
};
