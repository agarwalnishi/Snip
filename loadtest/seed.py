import asyncio
import hashlib

from sqlalchemy import insert

from app.base62 import random_code
from app.config import settings
from app.db import make_engine
from app.models import Link

N = 10_000


async def main():
    engine = make_engine(settings.database_url)
    rows, codes = [], []
    for i in range(N):
        url = f"https://example.com/page/{i}"
        code = random_code()
        codes.append(code)
        rows.append({"code": code, "long_url": url, "is_custom": False, "clicks": 0,
                     "url_hash": hashlib.sha256(url.encode()).hexdigest()})
    async with engine.begin() as conn:
        await conn.execute(insert(Link), rows)
    await engine.dispose()
    with open("loadtest/codes.txt", "w") as f:
        f.write("\n".join(codes))


asyncio.run(main())