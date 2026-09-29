import React from 'react';
import { Sparkles, Database, Layers, FileText } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { LiveClock } from '../ui/LiveClock';

export const Header: React.FC = () => {
  const { llmConfig, activeDocument, activeCitations, isDrawerOpen, setIsDrawerOpen } = useApp();

  return (
    <header className="h-16 border-b border-purple-500/20 glass-panel sticky top-0 z-30 px-6 flex items-center justify-between">
      {/* Brand logo & title */}
      <div className="flex items-center space-x-3">
        <div className="relative">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-700 via-violet-600 to-fuchsia-500 flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.5)]">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-black" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-purple-200 to-purple-400 bg-clip-text text-transparent">
              AuraRAG
            </h1>
            <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase bg-purple-900/50 text-purple-300 rounded border border-purple-500/30">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Transparent Document Intelligence & Agentic Engine
          </p>
        </div>
      </div>

      {/* Center status badges */}
      <div className="hidden md:flex items-center space-x-3">
        {/* LLM Status badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-purple-950/40 border border-purple-500/30 text-xs">
          <span className={`w-2 h-2 rounded-full ${llmConfig.isVerified ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-amber-400'}`} />
          <span className="text-slate-300 font-medium capitalize">{llmConfig.provider}:</span>
          <span className="text-purple-300 font-mono text-[11px]">{llmConfig.modelName}</span>
        </div>

        {/* Vector DB badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900/60 border border-purple-500/20 text-xs">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-300">ChromaDB + BM25</span>
          <span className="text-cyan-400 text-[10px] font-mono">Hybrid RRF</span>
        </div>

        {/* Active Document Indicator */}
        {activeDocument && (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-purple-900/30 border border-purple-500/40 text-xs max-w-[200px] truncate">
            <FileText className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
            <span className="text-slate-200 truncate font-medium text-[11px]">{activeDocument.filename}</span>
          </div>
        )}
      </div>

      {/* Right controls: Live Clock + Chunk Drawer Toggle */}
      <div className="flex items-center space-x-3">
        <LiveClock />

        {activeCitations.length > 0 && (
          <button
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isDrawerOpen
                ? 'bg-purple-600 text-white shadow-neon-glow'
                : 'bg-purple-950/60 text-purple-300 border border-purple-500/30 hover:border-purple-400/50'
            }`}
            title="Inspect retrieved passages"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Chunks ({activeCitations.length})</span>
          </button>
        )}
      </div>
    </header>
  );
};
