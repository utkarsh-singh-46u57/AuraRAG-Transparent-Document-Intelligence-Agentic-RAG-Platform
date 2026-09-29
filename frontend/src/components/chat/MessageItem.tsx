import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Sparkles, Copy, Check, Bookmark, Layers } from 'lucide-react';
import { Message, Citation } from '../../types';
import { ToolActivity } from './ToolActivity';
import { useApp } from '../../context/AppContext';

interface MessageItemProps {
  message: Message;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const { openCitationInPDF, setIsDrawerOpen, setActiveCitations } = useApp();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCitationClick = (citation: Citation) => {
    setActiveCitations(message.citations || [citation]);
    openCitationInPDF(citation);
  };

  return (
    <div className={`flex space-x-3.5 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-700 via-violet-600 to-fuchsia-500 flex items-center justify-center flex-shrink-0 shadow-neon-glow mt-1">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Message Bubble */}
      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 transition-all duration-200 ${
          isUser
            ? 'bg-purple-900/40 border border-purple-500/40 text-slate-100 shadow-glass rounded-tr-sm'
            : 'glass-panel border-purple-500/20 text-slate-100 rounded-tl-sm'
        }`}
      >
        {/* Header meta */}
        <div className="flex items-center justify-between mb-2 text-[11px] text-slate-400">
          <span className="font-semibold text-purple-300">
            {isUser ? 'You' : 'AuraRAG Assistant'}
          </span>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-[10px]">{message.timestamp}</span>
            {!isUser && (
              <button
                onClick={handleCopy}
                className="text-slate-400 hover:text-purple-300 p-0.5 rounded transition-colors"
                title="Copy response"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            )}
          </div>
        </div>

        {/* Tool Call Activities */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-3 space-y-1">
            {message.toolCalls.map((tc, idx) => (
              <ToolActivity key={idx} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Content Body */}
        <div className="prose prose-invert prose-purple max-w-none text-xs sm:text-sm leading-relaxed break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }: any) {
                return !inline ? (
                  <pre className="p-3 my-2 rounded-lg bg-black/60 border border-purple-500/25 overflow-x-auto text-xs font-mono text-purple-200">
                    <code className={className} {...props}>
                      {children}
                    </code>
                  </pre>
                ) : (
                  <code className="px-1.5 py-0.5 rounded bg-purple-950/60 border border-purple-500/30 text-purple-200 font-mono text-xs" {...props}>
                    {children}
                  </code>
                );
              },
              table({ children }: any) {
                return (
                  <div className="overflow-x-auto my-2">
                    <table className="min-w-full divide-y divide-purple-500/20 text-xs text-left">
                      {children}
                    </table>
                  </div>
                );
              }
            }}
          >
            {message.content}
          </ReactMarkdown>

          {message.isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-purple-400 animate-pulse align-middle" />
          )}
        </div>

        {/* Interactive Citations Bar */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-purple-500/15">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase font-semibold tracking-wider text-purple-400 flex items-center gap-1">
                <Bookmark className="w-3 h-3" />
                Verified Evidence Citations ({message.citations.length})
              </span>
              <button
                onClick={() => {
                  setActiveCitations(message.citations || []);
                  setIsDrawerOpen(true);
                }}
                className="text-[10px] text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1"
              >
                <Layers className="w-3 h-3" />
                Inspect All Chunks
              </button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {message.citations.map((c, idx) => (
                <button
                  key={c.chunk_id || idx}
                  onClick={() => handleCitationClick(c)}
                  className="group flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-black/50 hover:bg-purple-900/40 border border-cyan-500/30 hover:border-cyan-400 transition-all text-xs font-mono"
                  title="Click to view passage and coordinates in PDF"
                >
                  <span className="text-cyan-300 font-semibold group-hover:text-cyan-200">
                    Page {c.page}
                  </span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-400 text-[10px] group-hover:text-slate-200">
                    {c.chunk_id}
                  </span>
                  <span className="text-emerald-400 text-[10px]">
                    {Math.round(c.score * 100)}%
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-purple-950 border border-purple-500/30 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-purple-300" />
        </div>
      )}
    </div>
  );
};
