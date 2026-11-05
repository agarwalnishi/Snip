async def test_redirect_returns_302_to_long_url(client, make_code):
    code = await make_code("https://example.com/go")
    r = await client.get(f"/{code}")
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/go"


async def test_unknown_code_returns_404(client):
    r = await client.get("/nope123")
    assert r.status_code == 404


async def test_expired_link_returns_410(client, make_code, sql):
    code = await make_code("https://example.com/old", expires_in_minutes=5)
    await sql("UPDATE links SET expires_at = now() - interval '1 minute' WHERE code = :c", c=code)
    r = await client.get(f"/{code}")
    assert r.status_code == 410


async def test_alias_redirects(client):
    await client.post("/shorten", json={"url": "https://example.com/p", "alias": "promo"})
    r = await client.get("/promo")
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/p"