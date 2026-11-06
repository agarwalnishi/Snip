import asyncio
import logging
import uuid

from redis.exceptions import RedisError, ResponseError
from sqlalchemy import text

PENDING = "clicks:pending"
log = logging.getLogger("snip.clicks")

FLUSH_SQL = text("""
    UPDATE links SET clicks = links.clicks + d.n
    FROM unnest(CAST(:codes AS text[]), CAST(:ns AS bigint[])) AS d(code, n)
    WHERE links.code = d.code
""")


async def record_click(r, code: str) -> None:
    try:
        await r.hincrby(PENDING, code, 1)
    except RedisError:
        log.warning("redis unavailable, click for %s not counted", code)


async def flush_clicks(r, sessionmaker) -> int:
    batch_key = f"clicks:flushing:{uuid.uuid4().hex}"
    try:
        await r.rename(PENDING, batch_key)
    except ResponseError:
        return 0
    counts = await r.hgetall(batch_key)
    async with sessionmaker() as session:
        await session.execute(FLUSH_SQL, {
            "codes": list(counts.keys()),
            "ns": [int(v) for v in counts.values()],
        })
        await session.commit()
    await r.delete(batch_key)
    return len(counts)


async def flush_loop(r, sessionmaker, interval: int) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            n = await flush_clicks(r, sessionmaker)
            if n:
                log.info("flushed clicks for %d links", n)
        except Exception:
            log.exception("click flush failed")