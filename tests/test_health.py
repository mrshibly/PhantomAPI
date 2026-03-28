"""PhantomAPI — Basic endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client):
    """GET / should return 200 with status running."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["service"] == "PhantomAPI"


@pytest.mark.anyio
async def test_list_models(client):
    """GET /v1/models should return model list."""
    response = await client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0


@pytest.mark.anyio
async def test_chat_without_auth(client):
    """POST /v1/chat/completions without auth should return 401."""
    response = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_responses_without_auth(client):
    """POST /v1/responses without auth should return 401."""
    response = await client.post(
        "/v1/responses",
        json={"input": "Hello"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_gui_redirect(client):
    """GET /gui should redirect to the static GUI."""
    response = await client.get("/gui", follow_redirects=False)
    assert response.status_code == 307
