import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://snip:snip@localhost:5432/snip_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["FLUSH_INTERVAL"] = "3600"

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app


@pytest.fixture
async def client():
    async with LifespanManager(app):
        await app.state.redis.flushdb()
        async with app.state.sessionmaker() as s:
            await s.execute(text("TRUNCATE links RESTART IDENTITY"))
            await s.commit()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
def redis(client):
    return app.state.redis


@pytest.fixture
def make_code(client):
    async def _make(url, **extra):
        r = await client.post("/shorten", json={"url": url, **extra})
        assert r.status_code in (200, 201)
        return r.json()["code"]
    return _make


@pytest.fixture
def sql(client):
    async def _sql(query, **params):
        async with app.state.sessionmaker() as s:
            result = await s.execute(text(query), params)
            await s.commit()
            return result.scalar() if result.returns_rows else None
    return _sql