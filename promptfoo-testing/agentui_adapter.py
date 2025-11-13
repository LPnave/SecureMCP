"""
Agent-UI to Promptfoo Adapter
Translates between Agent-UI's security filter API and Promptfoo's expected format
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import uvicorn
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent-UI Promptfoo Adapter",
    description="Adapter to test Agent-UI security filter with Promptfoo"
)

# CORS for Promptfoo web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent-UI configuration
AGENT_UI_URL = "http://localhost:8003/api/sanitize"
ADAPTER_PORT = 8005

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Agent-UI Promptfoo Adapter",
        "status": "running",
        "agentui_url": AGENT_UI_URL,
        "endpoints": {
            "openai_compatible": "/v1/chat/completions",
            "simple": "/v1/completions"
        }
    }

@app.post("/v1/completions")
async def completions_endpoint(request: Request):
    """
    OpenAI-compatible completions endpoint for Promptfoo
    Accepts: {"prompt": "text", "model": "...", ...}
    Returns: OpenAI-style completion response
    """
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Call Agent-UI
        logger.info(f"Testing prompt: {prompt[:80]}...")
        agentui_response = call_agentui(prompt)
        
        # Transform to OpenAI format
        openai_response = transform_to_openai_format(prompt, agentui_response)
        
        return openai_response
        
    except Exception as e:
        logger.error(f"Error in completions endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completions_endpoint(request: Request):
    """
    OpenAI-compatible chat completions endpoint for Promptfoo
    Accepts: {"messages": [{"role": "user", "content": "text"}], ...}
    Returns: OpenAI-style chat completion response
    """
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required")
        
        # Extract last user message as the prompt
        prompt = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break
        
        if not prompt:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Call Agent-UI
        logger.info(f"Testing prompt: {prompt[:80]}...")
        agentui_response = call_agentui(prompt)
        
        # Transform to OpenAI chat format
        openai_response = transform_to_chat_format(prompt, agentui_response)
        
        return openai_response
        
    except Exception as e:
        logger.error(f"Error in chat completions endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def call_agentui(prompt: str) -> Dict[str, Any]:
    """
    Call Agent-UI security filter
    Returns the full response including security metadata
    """
    try:
        response = requests.post(
            AGENT_UI_URL,
            json={
                "prompt": prompt,
                "return_details": True
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Agent-UI: {e}")
        return {
            "error": str(e),
            "is_safe": True,
            "sanitized_prompt": prompt,
            "blocked_patterns": [],
            "warnings": []
        }

def transform_to_openai_format(prompt: str, agentui_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Agent-UI response to OpenAI completions format
    This is what Promptfoo will evaluate
    """
    # Extract security info
    is_safe = agentui_response.get("is_safe", True)
    blocked_patterns = agentui_response.get("blocked_patterns", [])
    sanitized = agentui_response.get("sanitized_prompt", prompt)
    warnings = agentui_response.get("warnings", [])
    
    # Build completion text that Promptfoo can evaluate
    if not is_safe or blocked_patterns:
        # Show that blocking occurred
        completion_text = f"[SECURITY BLOCKED: {', '.join(blocked_patterns)}] "
        completion_text += f"Sanitized output: {sanitized}"
        finish_reason = "content_filter"
    elif sanitized != prompt:
        # Sanitization occurred but not blocked
        completion_text = sanitized
        finish_reason = "stop"
    else:
        # Clean prompt, passed through
        completion_text = sanitized
        finish_reason = "stop"
    
    # Log for debugging
    logger.info(f"  Blocked: {not is_safe}")
    logger.info(f"  Patterns: {blocked_patterns}")
    logger.info(f"  Sanitized: {sanitized != prompt}")
    
    # Return OpenAI-compatible response
    return {
        "id": f"agentui-{int(time.time())}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": "agent-ui-security-filter",
        "choices": [{
            "text": completion_text,
            "index": 0,
            "finish_reason": finish_reason,
            "logprobs": None
        }],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(completion_text.split()),
            "total_tokens": len(prompt.split()) + len(completion_text.split())
        },
        # Include Agent-UI metadata for debugging
        "agentui_metadata": {
            "is_safe": is_safe,
            "blocked_patterns": blocked_patterns,
            "was_sanitized": sanitized != prompt,
            "warnings": warnings
        }
    }

def transform_to_chat_format(prompt: str, agentui_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Agent-UI response to OpenAI chat completions format
    """
    # Use same logic as completions
    base_response = transform_to_openai_format(prompt, agentui_response)
    
    # Convert to chat format
    return {
        "id": base_response["id"],
        "object": "chat.completion",
        "created": base_response["created"],
        "model": base_response["model"],
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": base_response["choices"][0]["text"]
            },
            "finish_reason": base_response["choices"][0]["finish_reason"]
        }],
        "usage": base_response["usage"],
        "agentui_metadata": base_response.get("agentui_metadata", {})
    }

if __name__ == "__main__":
    print("=" * 80)
    print("🔌 Agent-UI Promptfoo Adapter")
    print("=" * 80)
    print(f"\n✓ Starting adapter on: http://localhost:{ADAPTER_PORT}")
    print(f"✓ Forwarding to Agent-UI: {AGENT_UI_URL}")
    print(f"\n📝 Endpoints:")
    print(f"   - http://localhost:{ADAPTER_PORT}/v1/completions")
    print(f"   - http://localhost:{ADAPTER_PORT}/v1/chat/completions")
    print(f"\n🚀 Ready to accept Promptfoo requests!")
    print("=" * 80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=ADAPTER_PORT, log_level="info")

