"""PhantomAPI — GET /v1/models."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/models")
async def list_models():
    """Return available models for n8n model dropdown."""
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o-mini", "object": "model", "owned_by": "phantom-api"},
            {"id": "gpt-4o", "object": "model", "owned_by": "phantom-api"},
        ],
    }
