import time

from fastapi import HTTPException, Request

from app.config import settings


async def rate_limit(request: Request) -> None:
    r = request.app.state.redis
    ip = request.client.host if request.client else "unknown"
    window = int(time.time() // 60)
    key = f"rl:{ip}:{window}"

    async with r.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, 60)
        count, _ = await pipe.execute()

    if count > settings.rate_limit:
        retry_after = 60 - int(time.time() % 60)
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": str(retry_after)})