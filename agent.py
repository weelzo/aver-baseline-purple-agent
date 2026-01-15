#!/usr/bin/env python3
"""
AVER Baseline Purple Agent

A simple A2A-compliant agent for testing the AVER benchmark.
This is intentionally a "baseline" agent - it follows instructions
but has minimal error detection capabilities.

Designed to:
- Be A2A protocol compliant
- Work with OpenRouter (100+ models with one API key)
- Provide a baseline for AVER evaluation
- Be easily dockerized
"""

import os
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import uvicorn


# =============================================================================
# Configuration
# =============================================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("AGENT_MODEL", "anthropic/claude-3.5-sonnet")
PORT = int(os.getenv("AGENT_PORT", "8001"))
AGENT_NAME = os.getenv("AGENT_NAME", "AVER Baseline Purple Agent")

# OpenRouter API endpoint
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# =============================================================================
# Conversation Memory (per context_id)
# =============================================================================

conversation_history: Dict[str, List[Dict[str, str]]] = {}


def get_history(context_id: str) -> List[Dict[str, str]]:
    """Get conversation history for a context"""
    if context_id not in conversation_history:
        conversation_history[context_id] = []
    return conversation_history[context_id]


def add_to_history(context_id: str, role: str, content: str):
    """Add message to conversation history"""
    history = get_history(context_id)
    history.append({"role": role, "content": content})
    # Keep last 20 messages to avoid context overflow
    if len(history) > 20:
        conversation_history[context_id] = history[-20:]


def clear_history(context_id: Optional[str] = None):
    """Clear conversation history"""
    global conversation_history
    if context_id:
        conversation_history.pop(context_id, None)
    else:
        conversation_history = {}


# =============================================================================
# LLM Client
# =============================================================================

async def call_llm(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Call OpenRouter API to get LLM response

    Args:
        messages: Chat messages in OpenAI format
        model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Model response text
    """
    if not OPENROUTER_API_KEY:
        return "[ERROR] OPENROUTER_API_KEY not configured"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/aver-benchmark",
        "X-Title": AGENT_NAME,
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return f"[ERROR] API call failed: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"


# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """You are an AI assistant being evaluated on a benchmark task.

Your job is to:
1. Read the task description carefully
2. Use the available tools to complete the task
3. Provide your final answer

When responding, use this JSON format wrapped in <json></json> tags:
{
    "tool": "tool_name or 'respond' for final answer",
    "parameters": {"param": "value"},
    "reasoning": "Brief explanation of your action"
}

Available response types:
- Use a tool: {"tool": "tool_name", "parameters": {...}, "reasoning": "..."}
- Give final answer: {"tool": "respond", "parameters": {"message": "your answer"}, "reasoning": "..."}

Be direct and focused on completing the task efficiently."""


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print(f"\n{'='*60}")
    print(f"  {AGENT_NAME}")
    print(f"  Model: {DEFAULT_MODEL}")
    print(f"  Port: {PORT}")
    print(f"{'='*60}\n")

    if not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY not set!")
        print("Set it in .env or as environment variable")

    yield

    print("\nShutting down agent...")


app = FastAPI(
    title=AGENT_NAME,
    description="A2A-compliant baseline agent for AVER benchmark",
    lifespan=lifespan,
)


# =============================================================================
# A2A Protocol Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": AGENT_NAME,
        "status": "online",
        "model": DEFAULT_MODEL,
        "protocol": "A2A",
    }


@app.get("/agent-card")
async def agent_card():
    """
    A2A Agent Card - describes agent capabilities
    """
    return {
        "name": AGENT_NAME,
        "version": "1.0.0",
        "description": "Baseline purple agent for AVER benchmark evaluation",
        "capabilities": ["text-generation", "tool-use", "multi-turn"],
        "model": DEFAULT_MODEL,
        "protocol_version": "1.0",
    }


@app.post("/reset")
async def reset():
    """
    Reset agent state (called before each assessment)
    """
    clear_history()
    print("[Agent] State reset")
    return {"status": "reset", "message": "Agent state cleared"}


@app.post("/message")
async def handle_message(request: Request):
    """
    Main A2A message handler

    Receives messages from the green agent (AVER) and responds.
    """
    try:
        data = await request.json()

        # Extract message components
        role = data.get("role", "user")
        content = data.get("content", "")
        context_id = data.get("context_id", str(uuid.uuid4()))
        parent_id = data.get("message_id")

        # Check for model override
        metadata = data.get("metadata", {})
        model = metadata.get("model", DEFAULT_MODEL)

        print(f"\n[Received] context={context_id[:8]}...")
        print(f"[Content] {content[:200]}...")

        # Add user message to history
        add_to_history(context_id, "user", content)

        # Build messages for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *get_history(context_id)
        ]

        # Get response from LLM
        response_text = await call_llm(messages, model=model)

        # Add assistant response to history
        add_to_history(context_id, "assistant", response_text)

        print(f"[Response] {response_text[:200]}...")

        # Build A2A response
        message_id = str(uuid.uuid4())
        return JSONResponse({
            "role": "assistant",
            "content": response_text,
            "message_id": message_id,
            "context_id": context_id,
            "parent_id": parent_id,
            "metadata": {
                "model": model,
                "agent": AGENT_NAME,
            }
        })

    except Exception as e:
        print(f"[Error] {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/configure")
async def configure(request: Request):
    """
    Runtime configuration endpoint

    Allows changing model or other settings without restart.
    """
    global DEFAULT_MODEL

    data = await request.json()

    if "model" in data:
        DEFAULT_MODEL = data["model"]
        print(f"[Config] Model changed to: {DEFAULT_MODEL}")

    return {
        "status": "configured",
        "model": DEFAULT_MODEL,
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "agent:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
