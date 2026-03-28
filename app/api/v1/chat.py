"""PhantomAPI — POST /v1/chat/completions."""

from fastapi import APIRouter, Depends

from app.dependencies import verify_api_key
from app.schemas.chat import ChatCompletionRequest
from app.services.chat import process_chat_completion

router = APIRouter()


@router.post("/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(payload: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint."""
    data = payload.model_dump()
    return process_chat_completion(data["messages"], data["model"], data.get("tools"))
