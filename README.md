# Snip

A high-throughput URL shortener with Redis caching, built with FastAPI, PostgreSQL, Redis and Docker.
## Benchmark

Locust, 50 users for 2 minutes against 4 Uvicorn workers in Docker, on a Windows laptop. 10,000 seeded links; traffic is 90% to 200 hot links, 8% to any link, 2% to codes that don't exist.

| Run | Requests | Throughput | p50 (ms) | p95 (ms) | Cache hit rate |
| --- | --- | --- | --- | --- | --- |
| Cache off | 67,639 | 568 req/s | 14 | 300 | n/a |
| Cache on | 147,694 | 1,236 req/s | 6 | 13 | 93.3% |

The 2% of requests to non-existent codes return 404 by design; Locust reports them as failures. Locust and the API shared one laptop's CPU, so absolute latencies are higher than on dedicated hardware; the comparison between the two runs is what matters.