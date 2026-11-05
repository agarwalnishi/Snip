async def test_eleventh_create_in_a_minute_is_rate_limited(client):
    # can flake if it straddles a minute boundary (fixed window)
    for i in range(10):
        r = await client.post("/shorten", json={"url": f"https://example.com/{i}"})
        assert r.status_code == 201
    r = await client.post("/shorten", json={"url": "https://example.com/11"})
    assert r.status_code == 429
    assert "retry-after" in r.headers


async def test_redirects_are_not_rate_limited(client, make_code):
    code = await make_code("https://example.com/r")
    for _ in range(15):
        r = await client.get(f"/{code}")
        assert r.status_code == 302