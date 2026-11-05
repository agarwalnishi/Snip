import asyncio
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import models  # noqa: F401
from app.clicks import flush_clicks, flush_loop
from app.config import settings
from app.db import Base, get_session, make_engine
from app.routes import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.redis = redis.from_url(settings.redis_url, decode_responses=True)

    task = asyncio.create_task(
        flush_loop(app.state.redis, app.state.sessionmaker, settings.flush_interval)
    )
    yield
    task.cancel()
    await flush_clicks(app.state.redis, app.state.sessionmaker)
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(title="Snip", lifespan=lifespan)


@app.get("/health")
async def health(request: Request, session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))
    await request.app.state.redis.ping()
    return {"status": "ok"}


app.include_router(router)