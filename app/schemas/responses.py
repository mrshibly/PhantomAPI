"""PhantomAPI — Pydantic schemas for /v1/responses."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from app.schemas.chat import Message


class ResponsesRequest(BaseModel):
    """Request body for POST /v1/responses (Modern Responses API)."""
    input: Union[str, List[Message]] = Field(..., description="The input text or messages.")
    model: str = Field(default="gpt-4o-mini", description="Model identifier.")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="A list of tools the model may call.")
    instructions: Optional[str] = Field(default="", description="System instructions.")

    model_config = {"json_schema_extra": {"examples": [{"input": "Hello!", "model": "gpt-4o-mini"}]}}
