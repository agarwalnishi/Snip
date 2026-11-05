async def test_first_redirect_populates_cache(client, make_code, redis):
    code = await make_code("https://example.com/c1")
    assert await redis.get(f"link:{code}") is None
    await client.get(f"/{code}")
    assert await redis.get(f"link:{code}") == "https://example.com/c1"


async def test_cache_hit_needs_no_database(client, make_code, sql):
    code = await make_code("https://example.com/c2")
    await client.get(f"/{code}")               # warms the cache
    await sql("DELETE FROM links")              # database is now empty
    r = await client.get(f"/{code}")
    assert r.status_code == 302                 # only Redis could have answered


async def test_unknown_code_is_negative_cached(client, redis):
    await client.get("/ghost12")
    assert await redis.get("link:ghost12") == "__none__"
    assert 0 < await redis.ttl("link:ghost12") <= 60


async def test_creating_alias_clears_negative_cache(client):
    assert (await client.get("/sale2026")).status_code == 404
    await client.post("/shorten", json={"url": "https://example.com/s", "alias": "sale2026"})
    assert (await client.get("/sale2026")).status_code == 302


async def test_cache_ttl_capped_by_expiry(client, make_code, redis):
    code = await make_code("https://example.com/c3", expires_in_minutes=2)
    await client.get(f"/{code}")
    assert 0 < await redis.ttl(f"link:{code}") <= 120