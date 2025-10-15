/**
 * Chat API Route - Integrated with Python Backend
 * 
 * Flow:
 * 1. Frontend sends messages to this route
 * 2. This route forwards to Python backend
 * 3. Python backend sanitizes and calls local GPT-OSS
 * 4. Response is returned to frontend
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_SANITIZER_API_URL || 'http://localhost:8003';

interface Message {
  role: string;
  content: string;
}

interface ChatRequest {
  messages: Message[];
}

export async function POST(req: Request) {
  try {
    const { messages }: ChatRequest = await req.json();
    
    console.log(`[Chat] Received ${messages.length} messages`);
    
    // Forward to Python backend (which handles sanitization + GPT-OSS)
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages,
        security_level: 'medium',
        stream: false
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('[Chat] Backend error:', error);
      
      return new Response(
        JSON.stringify({
          error: error.detail || 'Failed to get response from AI',
          status: response.status
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    const data = await response.json();
    
    // Log sanitization info
    if (data.sanitization_applied) {
      console.log('[Chat] Sanitization was applied to the prompt');
      console.log('[Chat] Warnings:', data.warnings);
      if (data.original_prompt) {
        console.log('[Chat] Original:', data.original_prompt);
        console.log('[Chat] Sanitized:', data);
        console.log('[Chat] Sanitized:', data.message.content);
      }
    }
      // Return the AI message in the format expected by assistant-ui
      const aiMessage = data.message;
  
      console.log('[Chat] Full data received:', JSON.stringify(data, null, 2));
      console.log('[Chat] aiMessage:', aiMessage);
      console.log('[Chat] aiMessage.content:', aiMessage?.content);
      
      // Validate that we have content
      if (!aiMessage || !aiMessage.content) {
        console.error('[Chat] No content in response!', { data, aiMessage });
        throw new Error('No content in AI response');
      }
      
      const text = aiMessage.content;
      console.log('[Chat] Gemini response received, length:', text.length);
      console.log('[Chat] Response preview:', text.substring(0, 100));
      
    // Create a properly formatted stream for assistant-ui
    // Format: Vercel AI SDK v3 data stream protocol
    const encoder = new TextEncoder();
    
    const stream = new ReadableStream({
      start(controller) {
        try {
          // Stream text in chunks with proper protocol
          const chunkSize = 1; // Small chunks for smooth streaming effect
          for (let i = 0; i < text.length; i += chunkSize) {
            const chunk = text.slice(i, i + chunkSize);
            // Format: 0:"text"\n for text deltas
            controller.enqueue(encoder.encode(`0:${JSON.stringify(chunk)}\n`));
          }
          
          // Send finish message with proper metadata
          // Format: e:{"finishReason":"stop","usage":{...}}\n
          const finishData = {
            finishReason: 'stop',
            usage: { promptTokens: 0, completionTokens: text.length },
          };
          controller.enqueue(encoder.encode(`e:${JSON.stringify(finishData)}\n`));
          
          controller.close();
          console.log('[Chat Stream] Successfully streamed response');
        } catch (error) {
          console.error('[Chat Stream] Error:', error);
          controller.error(error);
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'X-Vercel-AI-Data-Stream': 'v1',
        'X-Sanitization-Applied': data.sanitization_applied.toString(),
        'X-Warnings': JSON.stringify(data.warnings),
      },
    });

  } catch (error) {
    console.error('[Chat] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
