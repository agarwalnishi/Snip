PENDING = "clicks:pending"


async def record_click(r, code: str) -> None:
    await r.hincrby(PENDING, code, 1)