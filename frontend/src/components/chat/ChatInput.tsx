import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Sparkles, Clock, Compass, FileSearch } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface ChatInputProps {
  onSendMessage: (query: string) => void;
  onStopStreaming: () => void;
  isStreaming: boolean;
}

const QUICK_PROMPTS = [
  { label: 'Apollo Lunar Module', query: 'What was the name of the Apollo 11 lunar module and commander?', icon: FileSearch },
  { label: 'Relative Date (+4d)', query: 'What date will it be 4 days from now?', icon: Clock },
  { label: 'Timezone Clock', query: 'What time is it in India right now?', icon: Clock },
  { label: 'Photosynthesis', query: 'Explain how photosynthesis works.', icon: Sparkles }
];

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onStopStreaming,
  isStreaming
}) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { activeDocument, ragMode } = useApp();

  const handleSend = () => {
    if (!text.trim() || isStreaming) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [text]);

  return (
    <div className="p-4 border-t border-purple-500/20 glass-panel relative z-20">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Quick Suggestion Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 no-scrollbar text-xs">
          <span className="text-[11px] text-slate-500 font-mono flex items-center gap-1 flex-shrink-0">
            <Compass className="w-3 h-3 text-purple-400" />
            Try:
          </span>
          {QUICK_PROMPTS.map((qp, idx) => {
            const Icon = qp.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => onSendMessage(qp.query)}
                disabled={isStreaming}
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-black/40 hover:bg-purple-950/60 border border-purple-500/20 hover:border-purple-400/50 text-slate-300 hover:text-purple-200 transition-all text-[11px] flex-shrink-0 disabled:opacity-40"
              >
                <Icon className="w-3 h-3 text-purple-400" />
                <span>{qp.label}</span>
              </button>
            );
          })}
        </div>

        {/* Input Textarea & Action Buttons */}
        <div className="relative flex items-end glass-input rounded-xl border border-purple-500/30 p-2 shadow-glass focus-within:border-purple-400 focus-within:shadow-neon-glow transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              activeDocument
                ? `Ask about ${activeDocument.filename}, or calculate dates/times...`
                : "Ask general knowledge questions or timezone date/time calculations..."
            }
            className="flex-1 bg-transparent border-0 resize-none text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-0 p-2 max-h-44"
          />

          <div className="flex items-center space-x-2 pb-1 pr-1 flex-shrink-0">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className="p-2 rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white transition-all shadow-md"
                title="Stop streaming"
              >
                <Square className="w-4 h-4 fill-white" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                disabled={!text.trim()}
                className="p-2 rounded-lg bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 disabled:opacity-40 text-white transition-all shadow-neon-glow"
                title="Send message (Enter)"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 px-1 font-mono">
          <span>Shift + Enter for new line • Enter to send</span>
          <span className="capitalize text-purple-400">Mode: {ragMode.replace('_', ' ')}</span>
        </div>
      </div>
    </div>
  );
};
