import type { SSEEvent } from '@/lib/types';
import { nanoid } from 'nanoid';

export const runtime = 'edge';

const BACKEND_URL = "https://gardening-environmental-crossing-strategic.trycloudflare.com/chat";
const TIMEOUT_MS = 30000;

async function fetchFromBackend(message: string, threadId: string): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, thread_id: threadId }),
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

function getLastUserMessage(messages: Array<{ role: string; parts?: Array<{ type: string; text?: string }>; content?: string }>): string | null {
  const lastMessage = messages[messages.length - 1];
  if (!lastMessage || lastMessage.role !== 'user') return null;

  if (lastMessage.parts) {
    const textPart = lastMessage.parts.find(p => p.type === 'text');
    return textPart?.text || null;
  }

  return lastMessage.content || null;
}

function sseEncode(data: unknown): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

function createTextStream(text: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const textPartId = nanoid();

  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(sseEncode({ type: 'text-start', id: textPartId })));
      controller.enqueue(encoder.encode(sseEncode({ type: 'text-delta', id: textPartId, delta: text })));
      controller.enqueue(encoder.encode(sseEncode({ type: 'text-end', id: textPartId })));
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });
}

export async function POST(req: Request) {
  const { messages } = await req.json();

  const userMessage = getLastUserMessage(messages);
  if (!userMessage) {
    return new Response('No user message found', { status: 400 });
  }

  const threadId = `thread-${Date.now()}`;

  let backendResponse: Response;
  try {
    backendResponse = await fetchFromBackend(userMessage, threadId);
  } catch (error) {
    const isTimeout = error instanceof Error && error.name === 'AbortError';
    const errorMessage = isTimeout
      ? 'The backend service is not responding. Please try again later.'
      : 'Unable to connect to the backend service. Please check if the service is running.';

    return new Response(createTextStream(errorMessage), {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'x-vercel-ai-ui-message-stream': 'v1',
      },
    });
  }

  if (!backendResponse.ok) {
    return new Response(createTextStream('The backend service returned an error. Please try again.'), {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'x-vercel-ai-ui-message-stream': 'v1',
      },
    });
  }

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const stream = new ReadableStream({
    async start(controller) {
      const reader = backendResponse.body?.getReader();
      if (!reader) {
        const textPartId = nanoid();
        controller.enqueue(encoder.encode(sseEncode({ type: 'text-start', id: textPartId })));
        controller.enqueue(encoder.encode(sseEncode({ type: 'text-delta', id: textPartId, delta: 'No response body from backend.' })));
        controller.enqueue(encoder.encode(sseEncode({ type: 'text-end', id: textPartId })));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
        return;
      }

      let buffer = '';
      const textPartId = nanoid();
      let textStarted = false;
      let textContent = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            // Trim to handle CRLF line endings
            const trimmedLine = line.trim();
            if (trimmedLine === 'data: [DONE]') {
              // Handle SSE done signal
              continue;
            }
            if (trimmedLine.startsWith('data: ')) {
              try {
                const sseData = JSON.parse(trimmedLine.slice(6)) as SSEEvent;

                switch (sseData.type) {
                  case 'agent':
                    if (!textStarted) {
                      controller.enqueue(encoder.encode(sseEncode({ type: 'text-start', id: textPartId })));
                      textStarted = true;
                    }
                    controller.enqueue(encoder.encode(sseEncode({ type: 'text-delta', id: textPartId, delta: sseData.content })));
                    textContent += sseData.content;
                    break;

                  case 'tool':
                    controller.enqueue(encoder.encode(sseEncode({
                      type: 'data-tool-output',
                      data: { content: sseData.content },
                    })));
                    break;

                  case 'events':
                    controller.enqueue(encoder.encode(sseEncode({
                      type: 'data-validation',
                      data: { events: sseData.events },
                    })));
                    break;

                  case 'error':
                    if (!textStarted) {
                      controller.enqueue(encoder.encode(sseEncode({ type: 'text-start', id: textPartId })));
                      textStarted = true;
                    }
                    controller.enqueue(encoder.encode(sseEncode({ type: 'text-delta', id: textPartId, delta: `Error: ${sseData.content}` })));
                    break;

                  case 'done':
                    break;
                }
              } catch {
                // Skip malformed SSE data
              }
            }
          }
        }

        if (textStarted) {
          controller.enqueue(encoder.encode(sseEncode({ type: 'text-end', id: textPartId })));
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      } catch {
        if (!textStarted) {
          controller.enqueue(encoder.encode(sseEncode({ type: 'text-start', id: textPartId })));
        }
        controller.enqueue(encoder.encode(sseEncode({ type: 'text-delta', id: textPartId, delta: 'Stream processing failed.' })));
        controller.enqueue(encoder.encode(sseEncode({ type: 'text-end', id: textPartId })));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'x-vercel-ai-ui-message-stream': 'v1',
    },
  });
}
