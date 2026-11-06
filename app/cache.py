import logging
from datetime import datetime, timezone

from redis.exceptions import RedisError

log = logging.getLogger("snip.cache")
MISSING = "__none__"


def key(code: str) -> str:
    return f"link:{code}"


async def get(r, code: str) -> str | None:
    try:
        return await r.get(key(code))
    except RedisError:
        log.warning("redis unavailable, treating %s as a cache miss", code)
        return None


async def set_link(r, code: str, long_url: str, expires_at: datetime | None, ttl: int) -> None:
    if expires_at is not None:
        remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if remaining <= 0:
            return
        ttl = min(ttl, remaining)
    try:
        await r.set(key(code), long_url, ex=ttl)
    except RedisError:
        log.warning("redis unavailable, could not cache %s", code)


async def set_missing(r, code: str, ttl: int) -> None:
    try:
        await r.set(key(code), MISSING, ex=ttl)
    except RedisError:
        log.warning("redis unavailable, could not negative-cache %s", code)


async def invalidate(r, code: str) -> None:
    try:
        await r.delete(key(code))
    except RedisError:
        log.warning("redis unavailable, could not invalidate %s", code)