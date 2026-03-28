"""PhantomAPI — Application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1.router import router as v1_router
from app.services.browser import engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Start the browser engine on startup."""
    engine.start()
    yield


app = FastAPI(
    title="PhantomAPI",
    description="A proxy that turns free ChatGPT into an OpenAI-compatible API.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", tags=["health"])
async def health_check():
    """Health check."""
    return {"status": "running", "service": "PhantomAPI", "version": __version__}


@app.get("/gui", tags=["gui"])
async def gui_redirect():
    """Redirect to Chat GUI."""
    return RedirectResponse(url="/static/index.html")
