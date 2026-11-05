import asyncio

from app import models  # noqa: F401
from app.config import settings
from app.db import Base, make_engine


async def main():
    engine = make_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())