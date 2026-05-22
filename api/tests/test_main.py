import pytest
from httpx import ASGITransport, AsyncClient

from api.src.main import app


@pytest.mark.asyncio
async def test_app_starts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "tradehunt-api"}
