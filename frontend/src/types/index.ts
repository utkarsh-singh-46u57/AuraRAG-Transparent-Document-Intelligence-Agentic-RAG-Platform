export interface Citation {
  chunk_id: string;
  page: number;
  paragraph?: number;
  score: number;
  text: string;
  bbox?: number[]; // [x0, y0, x1, y1] normalized percentages
  heading?: string;
}

export interface ToolCallEvent {
  tool: string;
  args: Record<string, any>;
  result?: Record<string, any>;
  status: 'running' | 'completed' | 'failed';
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  citations?: Citation[];
  toolCalls?: ToolCallEvent[];
  isStreaming?: boolean;
}

export interface DocumentMeta {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  char_count: number;
  status: string;
  is_scanned?: boolean;
}

export interface DocumentChunk {
  chunk_id: string;
  document_id: string;
  page_number: number;
  paragraph_number: number;
  section_heading?: string;
  text: string;
  bbox?: number[];
  char_count: number;
}

export type RAGMode = 'auto' | 'document_only' | 'general_ai';

export interface LLMConfig {
  provider: 'gemini' | 'openai';
  apiKey: string;
  modelName: string;
  isVerified: boolean;
}
