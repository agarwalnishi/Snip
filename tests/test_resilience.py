from redis.exceptions import ConnectionError as RedisConnectionError


async def test_redirect_works_when_redis_is_down(client, make_code, redis, monkeypatch):
    code = await make_code("https://example.com/down")

    async def broken(*args, **kwargs):
        raise RedisConnectionError("redis is down")

    monkeypatch.setattr(redis, "get", broken)
    monkeypatch.setattr(redis, "set", broken)
    monkeypatch.setattr(redis, "hincrby", broken)

    r = await client.get(f"/{code}")
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/down"