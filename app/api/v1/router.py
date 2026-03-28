"""PhantomAPI — v1 API router aggregator."""

from fastapi import APIRouter

from app.api.v1 import chat, responses, models

router = APIRouter(prefix="/v1", tags=["v1"])

router.include_router(chat.router)
router.include_router(responses.router)
router.include_router(models.router)
