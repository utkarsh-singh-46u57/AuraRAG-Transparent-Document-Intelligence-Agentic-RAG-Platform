import React, { useState, useRef } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ChatContainer } from './components/chat/ChatContainer';
import { ChunkDrawer } from './components/inspection/ChunkDrawer';
import { PDFViewerModal } from './components/pdf/PDFViewerModal';
import { Message, Citation, ToolCallEvent } from './types';
import { useApp } from './context/AppContext';
import { streamChatResponse } from './services/sse';

export const App: React.FC = () => {
  const {
    sessionId,
    activeDocument,
    llmConfig,
    ragMode,
    timezone,
    setActiveCitations
  } = useApp();

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleSendMessage = async (query: string) => {
    if (!query.trim() || isStreaming) return;

    const userMessageId = 'msg_' + Date.now();
    const assistantMessageId = 'msg_' + (Date.now() + 1);
    const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMsg: Message = {
      id: userMessageId,
      role: 'user',
      content: query,
      timestamp: timestampStr
    };

    const initialAssistantMsg: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: timestampStr,
      isStreaming: true,
      citations: [],
      toolCalls: []
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const recentHistory = messages.slice(-6).map((m) => ({
      role: m.role,
      content: m.content
    }));

    const streamPayload = {
      query,
      session_id: sessionId,
      document_id: activeDocument?.document_id || null,
      rag_mode: ragMode,
      provider: llmConfig.provider,
      model_name: llmConfig.modelName,
      api_key: llmConfig.apiKey || null,
      timezone,
      history: recentHistory
    };

    await streamChatResponse(
      streamPayload,
      {
        onCitation: (citations: Citation[]) => {
          setActiveCitations(citations);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, citations }
                : m
            )
          );
        },
        onToolStart: (tool: string, args: Record<string, any>) => {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== assistantMessageId) return m;
              const newTool: ToolCallEvent = { tool, args, status: 'running' };
              return {
                ...m,
                toolCalls: [...(m.toolCalls || []), newTool]
              };
            })
          );
        },
        onToolEnd: (tool: string, result: Record<string, any>) => {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== assistantMessageId) return m;
              const updated = (m.toolCalls || []).map((tc) =>
                tc.tool === tool ? { ...tc, result, status: 'completed' as const } : tc
              );
              return { ...m, toolCalls: updated };
            })
          );
        },
        onDelta: (text: string) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, content: m.content + text }
                : m
            )
          );
        },
        onDone: () => {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, isStreaming: false }
                : m
            )
          );
          abortControllerRef.current = null;
        },
        onError: (err: Error) => {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? {
                    ...m,
                    content: m.content + `\n\n*[Error: ${err.message}]*`,
                    isStreaming: false
                  }
                : m
            )
          );
          abortControllerRef.current = null;
        }
      },
      abortController.signal
    );
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    );
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#07060a] text-slate-100">
      {/* Top Navbar */}
      <Header />

      {/* Main Workspace: Sidebar + Chat Feed */}
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar />
        <ChatContainer
          messages={messages}
          isStreaming={isStreaming}
          onSendMessage={handleSendMessage}
          onStopStreaming={handleStopStreaming}
        />
      </div>

      {/* Synchronized Drawers & Modals */}
      <ChunkDrawer />
      <PDFViewerModal />
    </div>
  );
};
export default App;
