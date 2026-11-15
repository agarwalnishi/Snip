async def test_metrics_count_hits_misses_and_not_found(client, make_code):
    code = await make_code("https://example.com/m")
    await client.get(f"/{code}")      # first visit: cache miss
    await client.get(f"/{code}")      # second visit: cache hit
    await client.get("/nope999")      # unknown code: miss and 404

    r = await client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "snip_links_created_total 1" in body
    assert "snip_cache_hits_total 1" in body
    assert "snip_cache_misses_total 2" in body
    assert "snip_not_found_total 1" in body