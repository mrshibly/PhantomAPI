"""PhantomAPI — Authentication dependencies."""

from fastapi import Request, HTTPException
from app.config import settings


async def verify_api_key(request: Request) -> str:
    """Validate the Bearer token from the Authorization header.

    Returns the validated key on success, raises 401 on failure.
    """
    authorization = request.headers.get("authorization", "")

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    # Strip "Bearer " prefix
    token = authorization.replace("Bearer ", "").strip()

    if token != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key.")

    return token
