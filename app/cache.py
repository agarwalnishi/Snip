from datetime import datetime, timezone

MISSING = "__none__"


def key(code: str) -> str:
    return f"link:{code}"


async def get(r, code: str) -> str | None:
    return await r.get(key(code))


async def set_link(r, code: str, long_url: str, expires_at: datetime | None, ttl: int) -> None:
    if expires_at is not None:
        remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if remaining <= 0:
            return
        ttl = min(ttl, remaining)
    await r.set(key(code), long_url, ex=ttl)


async def set_missing(r, code: str, ttl: int) -> None:
    await r.set(key(code), MISSING, ex=ttl)


async def invalidate(r, code: str) -> None:
    await r.delete(key(code))