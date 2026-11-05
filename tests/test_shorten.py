from datetime import datetime, timedelta, timezone


async def test_shorten_returns_201_and_7_char_code(client):
    r = await client.post("/shorten", json={"url": "https://example.com/a"})
    assert r.status_code == 201
    assert len(r.json()["code"]) == 7


async def test_same_url_is_deduplicated(client):
    first = await client.post("/shorten", json={"url": "https://example.com/dup"})
    second = await client.post("/shorten", json={"url": "https://example.com/dup"})
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["code"] == second.json()["code"]


async def test_different_urls_get_different_codes(client, make_code):
    a = await make_code("https://example.com/one")
    b = await make_code("https://example.com/two")
    assert a != b


async def test_invalid_url_rejected(client):
    r = await client.post("/shorten", json={"url": "not a url"})
    assert r.status_code == 422


async def test_custom_alias_is_used(client):
    r = await client.post("/shorten", json={"url": "https://example.com", "alias": "launch"})
    assert r.status_code == 201
    assert r.json()["code"] == "launch"


async def test_duplicate_alias_returns_409(client):
    await client.post("/shorten", json={"url": "https://example.com", "alias": "taken"})
    r = await client.post("/shorten", json={"url": "https://example.org", "alias": "taken"})
    assert r.status_code == 409


async def test_reserved_alias_returns_400(client):
    r = await client.post("/shorten", json={"url": "https://example.com", "alias": "docs"})
    assert r.status_code == 400


async def test_alias_with_bad_characters_returns_422(client):
    r = await client.post("/shorten", json={"url": "https://example.com", "alias": "my link"})
    assert r.status_code == 422


async def test_expiring_link_is_not_deduplicated(client):
    perm = await client.post("/shorten", json={"url": "https://example.com/x"})
    temp = await client.post("/shorten", json={"url": "https://example.com/x", "expires_in_minutes": 5})
    assert temp.status_code == 201
    assert temp.json()["code"] != perm.json()["code"]


async def test_expires_at_is_set(client):
    r = await client.post("/shorten", json={"url": "https://example.com/t", "expires_in_minutes": 10})
    expires_at = datetime.fromisoformat(r.json()["expires_at"])
    left = expires_at - datetime.now(timezone.utc)
    assert timedelta(minutes=9) < left <= timedelta(minutes=10)