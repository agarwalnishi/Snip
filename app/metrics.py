from redis.exceptions import RedisError

PREFIX = "metrics:"
NAMES = ("cache_hits", "cache_misses", "not_found", "links_created")


async def bump(r, name: str) -> None:
    try:
        await r.incr(PREFIX + name)
    except RedisError:
        pass


async def snapshot(r) -> dict[str, int]:
    values = await r.mget([PREFIX + n for n in NAMES])
    return {n: int(v or 0) for n, v in zip(NAMES, values)}


def to_prometheus(counts: dict[str, int]) -> str:
    lines = []
    for name, value in counts.items():
        lines.append(f"# TYPE snip_{name}_total counter")
        lines.append(f"snip_{name}_total {value}")
    lookups = counts["cache_hits"] + counts["cache_misses"]
    ratio = counts["cache_hits"] / lookups if lookups else 0.0
    lines.append("# TYPE snip_cache_hit_ratio gauge")
    lines.append(f"snip_cache_hit_ratio {ratio:.4f}")
    return "\n".join(lines) + "\n"