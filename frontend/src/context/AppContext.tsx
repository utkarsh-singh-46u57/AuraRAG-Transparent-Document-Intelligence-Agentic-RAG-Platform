import React, { createContext, useContext, useState, useEffect } from 'react';
import { DocumentMeta, LLMConfig, RAGMode, Citation } from '../types';

interface AppContextType {
  sessionId: string;
  activeDocument: DocumentMeta | null;
  setActiveDocument: (doc: DocumentMeta | null) => void;
  llmConfig: LLMConfig;
  setLLMConfig: React.Dispatch<React.SetStateAction<LLMConfig>>;
  ragMode: RAGMode;
  setRAGMode: (mode: RAGMode) => void;
  timezone: string;
  setTimezone: (tz: string) => void;
  activeCitations: Citation[];
  setActiveCitations: (c: Citation[]) => void;
  selectedCitation: Citation | null;
  setSelectedCitation: (c: Citation | null) => void;
  isDrawerOpen: boolean;
  setIsDrawerOpen: (open: boolean) => void;
  isPDFModalOpen: boolean;
  setIsPDFModalOpen: (open: boolean) => void;
  currentPDFPage: number;
  setCurrentPDFPage: (p: number) => void;
  highlightBbox: number[] | null;
  setHighlightBbox: (b: number[] | null) => void;
  openCitationInPDF: (c: Citation) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessionId] = useState<string>(() => {
    const saved = localStorage.getItem('aurarag_session_id');
    if (saved) return saved;
    const generated = 'sess_' + Math.random().toString(36).substring(2, 11);
    localStorage.setItem('aurarag_session_id', generated);
    return generated;
  });

  const [activeDocument, setActiveDocument] = useState<DocumentMeta | null>(() => {
    const saved = localStorage.getItem('aurarag_active_doc');
    return saved ? JSON.parse(saved) : null;
  });

  const [llmConfig, setLLMConfig] = useState<LLMConfig>(() => {
    const savedKey = localStorage.getItem('aurarag_api_key') || '';
    const savedProvider = (localStorage.getItem('aurarag_provider') as any) || 'gemini';
    const savedModel = localStorage.getItem('aurarag_model') || 'gemini-3.8-flash';
    return {
      provider: savedProvider,
      apiKey: savedKey,
      modelName: savedModel,
      isVerified: savedKey.length > 0
    };
  });

  const [ragMode, setRAGMode] = useState<RAGMode>('auto');

  const [timezone, setTimezone] = useState<string>(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';
    } catch {
      return 'UTC';
    }
  });

  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isPDFModalOpen, setIsPDFModalOpen] = useState<boolean>(false);
  const [currentPDFPage, setCurrentPDFPage] = useState<number>(1);
  const [highlightBbox, setHighlightBbox] = useState<number[] | null>(null);

  useEffect(() => {
    if (activeDocument) {
      localStorage.setItem('aurarag_active_doc', JSON.stringify(activeDocument));
    } else {
      localStorage.removeItem('aurarag_active_doc');
    }
  }, [activeDocument]);

  useEffect(() => {
    if (llmConfig.apiKey) {
      localStorage.setItem('aurarag_api_key', llmConfig.apiKey);
      localStorage.setItem('aurarag_provider', llmConfig.provider);
      localStorage.setItem('aurarag_model', llmConfig.modelName);
    }
  }, [llmConfig]);

  const openCitationInPDF = (citation: Citation) => {
    setSelectedCitation(citation);
    setCurrentPDFPage(citation.page);
    setHighlightBbox(citation.bbox || null);
    setIsPDFModalOpen(true);
  };

  return (
    <AppContext.Provider
      value={{
        sessionId,
        activeDocument,
        setActiveDocument,
        llmConfig,
        setLLMConfig,
        ragMode,
        setRAGMode,
        timezone,
        setTimezone,
        activeCitations,
        setActiveCitations,
        selectedCitation,
        setSelectedCitation,
        isDrawerOpen,
        setIsDrawerOpen,
        isPDFModalOpen,
        setIsPDFModalOpen,
        currentPDFPage,
        setCurrentPDFPage,
        highlightBbox,
        setHighlightBbox,
        openCitationInPDF
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
