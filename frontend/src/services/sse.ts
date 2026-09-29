import { Citation, ToolCallEvent } from '../types';

export interface StreamCallbacks {
  onCitation?: (citations: Citation[]) => void;
  onToolStart?: (tool: string, args: Record<string, any>) => void;
  onToolEnd?: (tool: string, result: Record<string, any>) => void;
  onDelta?: (text: string) => void;
  onDone?: (finishReason: string) => void;
  onError?: (err: Error) => void;
}

export async function streamChatResponse(
  payload: Record<string, any>,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
) {
  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify(payload),
      signal
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Failed to initiate chat stream' }));
      throw new Error(err.detail || `HTTP Error ${response.status}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported by browser/server');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = 'message';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          currentEvent = 'message';
          continue;
        }

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.replace('event:', '').trim();
        } else if (trimmed.startsWith('data:')) {
          const dataStr = trimmed.replace('data:', '').trim();
          try {
            const dataObj = JSON.parse(dataStr);
            if (currentEvent === 'citation' && callbacks.onCitation) {
              callbacks.onCitation(dataObj.citations || []);
            } else if (currentEvent === 'tool_start' && callbacks.onToolStart) {
              callbacks.onToolStart(dataObj.tool, dataObj.args || {});
            } else if (currentEvent === 'tool_end' && callbacks.onToolEnd) {
              callbacks.onToolEnd(dataObj.tool, dataObj.result || {});
            } else if (currentEvent === 'delta' && callbacks.onDelta) {
              callbacks.onDelta(dataObj.text || '');
            } else if (currentEvent === 'done' && callbacks.onDone) {
              callbacks.onDone(dataObj.finish_reason || 'stop');
            }
          } catch (e) {
            // Raw text delta fallback
            if (currentEvent === 'delta' && callbacks.onDelta) {
              callbacks.onDelta(dataStr);
            }
          }
        }
      }
    }

    if (callbacks.onDone) {
      callbacks.onDone('stop');
    }
  } catch (error: any) {
    if (error.name === 'AbortError') return;
    if (callbacks.onError) {
      callbacks.onError(error);
    }
  }
}
