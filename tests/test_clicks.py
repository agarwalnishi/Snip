from app.clicks import flush_clicks
from app.main import app


async def test_clicks_pending_in_redis_before_flush(client, make_code, redis):
    code = await make_code("https://example.com/k1")
    for _ in range(3):
        await client.get(f"/{code}")
    assert await redis.hget("clicks:pending", code) == "3"


async def test_flush_writes_clicks_to_postgres(client, make_code, redis, sql):
    code = await make_code("https://example.com/k2")
    for _ in range(3):
        await client.get(f"/{code}")
    assert await flush_clicks(redis, app.state.sessionmaker) == 1
    assert await sql("SELECT clicks FROM links WHERE code = :c", c=code) == 3
    assert await redis.exists("clicks:pending") == 0


async def test_flush_with_nothing_pending_returns_zero(client, redis):
    assert await flush_clicks(redis, app.state.sessionmaker) == 0