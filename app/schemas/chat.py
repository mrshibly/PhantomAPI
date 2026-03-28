"""PhantomAPI — Pydantic schemas for /v1/chat/completions."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., description="The role of the message author.")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="The content of the message.")
    name: Optional[str] = Field(default=None, description="Name for tool messages.")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Tool calls from assistant.")
    tool_call_id: Optional[str] = Field(default=None, description="Tool call ID for tool responses.")


class ChatCompletionRequest(BaseModel):
    """Request body for POST /v1/chat/completions."""
    messages: List[Message] = Field(..., description="The conversation messages.")
    model: str = Field(default="gpt-4o-mini", description="Model identifier.")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="Available tools for function calling.")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature (ignored).")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens (ignored).")

    model_config = {
        "json_schema_extra": {
            "examples": [{"messages": [{"role": "user", "content": "Hello!"}], "model": "gpt-4o-mini"}]
        }
    }
