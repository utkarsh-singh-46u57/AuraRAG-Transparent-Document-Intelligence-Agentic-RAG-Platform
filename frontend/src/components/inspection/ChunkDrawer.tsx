import React from 'react';
import { X, Layers, ExternalLink, Bookmark, Hash } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreBadge } from './ScoreBadge';

export const ChunkDrawer: React.FC = () => {
  const {
    isDrawerOpen,
    setIsDrawerOpen,
    activeCitations,
    openCitationInPDF
  } = useApp();

  if (!isDrawerOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 transition-opacity"
        onClick={() => setIsDrawerOpen(false)}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-lg glass-panel border-l border-purple-500/30 z-50 flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        
        {/* Header */}
        <div className="h-16 px-6 border-b border-purple-500/20 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Layers className="w-5 h-5 text-purple-400" />
            <div>
              <h2 className="text-sm font-semibold text-slate-100">
                Retrieved Context Chunks
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                {activeCitations.length} passages passed to LLM
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsDrawerOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Chunks List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {activeCitations.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No chunks retrieved for the active response.
            </div>
          ) : (
            activeCitations.map((chunk, idx) => (
              <div
                key={chunk.chunk_id || idx}
                className="glass-card p-4 rounded-xl space-y-3 border-purple-500/25 hover:border-purple-400/50"
              >
                {/* Chunk Meta Header */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded bg-purple-950/70 border border-purple-500/40 text-purple-300 font-mono text-[11px] font-semibold">
                      Page {chunk.page}
                    </span>
                    <span className="text-slate-400 font-mono text-[10px] flex items-center">
                      <Hash className="w-3 h-3 mr-0.5 text-slate-500" />
                      {chunk.chunk_id}
                    </span>
                  </div>
                  <ScoreBadge score={chunk.score} />
                </div>

                {/* Section Heading if available */}
                {chunk.heading && (
                  <div className="flex items-center space-x-1.5 text-xs text-purple-200/90 font-medium">
                    <Bookmark className="w-3.5 h-3.5 text-purple-400" />
                    <span>{chunk.heading}</span>
                  </div>
                )}

                {/* Raw Text Box */}
                <div className="p-3 rounded-lg bg-black/40 border border-purple-500/15 text-xs text-slate-300 font-mono leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap select-text">
                  {chunk.text}
                </div>

                {/* Jump to PDF button */}
                <div className="flex justify-end pt-1">
                  <button
                    onClick={() => openCitationInPDF(chunk)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/30 text-purple-200 text-xs font-medium transition-all"
                  >
                    <span>View in PDF</span>
                    <ExternalLink className="w-3 h-3 text-purple-300" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
};
