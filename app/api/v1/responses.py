"""PhantomAPI — POST /v1/responses."""

from fastapi import APIRouter, Depends

from app.dependencies import verify_api_key
from app.schemas.responses import ResponsesRequest
from app.services.chat import process_responses_api

router = APIRouter()


@router.post("/responses", dependencies=[Depends(verify_api_key)])
async def responses(payload: ResponsesRequest):
    """Modern Responses API endpoint for newer n8n versions."""
    data = payload.model_dump()
    input_data = data.get("input", "")

    # Normalise input to messages list
    if isinstance(input_data, str):
        messages = [{"role": "user", "content": input_data}]
    elif isinstance(input_data, list):
        messages = input_data
    else:
        messages = []

    # Inject system instructions
    instructions = data.get("instructions", "")
    if instructions:
        messages.insert(0, {"role": "system", "content": instructions})

    return process_responses_api(messages, data["model"], data.get("tools"))
