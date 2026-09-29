import { DocumentMeta, DocumentChunk } from '../types';

const API_BASE = '/api';

export async function verifyLLMKey(provider: string, apiKey: string, modelName?: string) {
  const resp = await fetch(`${API_BASE}/llm/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider,
      api_key: apiKey,
      model_name: modelName
    })
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({ detail: 'Failed to verify key' }));
    throw new Error(errorData.detail || 'Verification failed');
  }
  return resp.json();
}

export async function uploadDocument(file: File, sessionId: string, provider: string, apiKey: string): Promise<DocumentMeta> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  formData.append('provider', provider);
  if (apiKey) formData.append('api_key', apiKey);

  const resp = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || 'Failed to upload document');
  }
  return resp.json();
}

export async function getDocumentStatus(docId: string) {
  const resp = await fetch(`${API_BASE}/documents/status/${docId}`);
  if (!resp.ok) throw new Error('Failed to fetch document status');
  return resp.json();
}

export async function getDocumentChunks(docId: string, page = 1, pageSize = 50): Promise<{ total_chunks: number; chunks: DocumentChunk[] }> {
  const resp = await fetch(`${API_BASE}/documents/${docId}/chunks?page=${page}&page_size=${pageSize}`);
  if (!resp.ok) throw new Error('Failed to fetch document chunks');
  return resp.json();
}

export async function deleteDocument(docId: string, sessionId?: string) {
  const url = sessionId ? `${API_BASE}/documents/${docId}?session_id=${sessionId}` : `${API_BASE}/documents/${docId}`;
  const resp = await fetch(url, { method: 'DELETE' });
  if (!resp.ok) throw new Error('Failed to delete document');
  return resp.json();
}

export async function getCurrentTime(timezone = 'UTC') {
  const resp = await fetch(`${API_BASE}/tools/time?timezone=${encodeURIComponent(timezone)}`);
  if (!resp.ok) throw new Error('Failed to fetch time');
  return resp.json();
}

export function getDocumentFileUrl(docId: string, sessionId?: string): string {
  return sessionId ? `${API_BASE}/documents/${docId}/file?session_id=${sessionId}` : `${API_BASE}/documents/${docId}/file`;
}
