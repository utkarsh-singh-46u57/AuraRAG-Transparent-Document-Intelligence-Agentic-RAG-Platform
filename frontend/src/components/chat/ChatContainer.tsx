import React, { useRef, useEffect } from 'react';
import { MessageItem } from './MessageItem';
import { ChatInput } from './ChatInput';
import { Message } from '../../types';
import { Sparkles, ShieldCheck, Zap, FileSearch } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface ChatContainerProps {
  messages: Message[];
  isStreaming: boolean;
  onSendMessage: (query: string) => void;
  onStopStreaming: () => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isStreaming,
  onSendMessage,
  onStopStreaming
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { activeDocument } = useApp();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] overflow-hidden relative">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-4">
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="max-w-2xl mx-auto py-12 text-center space-y-8 animate-in fade-in duration-300">
            <div className="space-y-3">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-700 via-violet-600 to-fuchsia-500 flex items-center justify-center shadow-neon-glow mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-white animate-pulse" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-white via-purple-100 to-purple-400 bg-clip-text text-transparent">
                AuraRAG Intelligent Workspace
              </h2>
              <p className="text-sm text-slate-400 max-w-lg mx-auto leading-relaxed">
                Deterministic Document Intelligence, Gemini native function-calling tools,
                and transparent coordinate citations.
              </p>
            </div>

            {/* Feature Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
              <div className="glass-card p-4 rounded-xl space-y-2 border-purple-500/20">
                <FileSearch className="w-5 h-5 text-cyan-400" />
                <h3 className="text-xs font-semibold text-slate-200">Verifiable Evidence</h3>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Every document answer is linked directly to exact page and paragraph bounding boxes.
                </p>
              </div>

              <div className="glass-card p-4 rounded-xl space-y-2 border-purple-500/20">
                <Zap className="w-5 h-5 text-amber-400" />
                <h3 className="text-xs font-semibold text-slate-200">Authoritative Tools</h3>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Real-time timezone clock queries and relative date arithmetic via native LLM tool execution.
                </p>
              </div>

              <div className="glass-card p-4 rounded-xl space-y-2 border-purple-500/20">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-xs font-semibold text-slate-200">Anti-Injection RAG</h3>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Hybrid BM25 + dense ChromaDB retrieval with strict XML untrusted isolation barriers.
                </p>
              </div>
            </div>

            {activeDocument ? (
              <div className="p-3 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs text-purple-200 font-mono inline-block">
                Active Document: <span className="font-semibold text-white">{activeDocument.filename}</span> ({activeDocument.chunk_count} chunks indexed)
              </div>
            ) : (
              <p className="text-xs text-slate-500 font-mono">
                Upload a PDF in the sidebar or ask timezone/general questions below to get started.
              </p>
            )}
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((m) => (
              <MessageItem key={m.id} message={m} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <ChatInput
        onSendMessage={onSendMessage}
        onStopStreaming={onStopStreaming}
        isStreaming={isStreaming}
      />
    </div>
  );
};
