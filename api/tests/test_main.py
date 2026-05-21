import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_app_starts():
    from api.src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
