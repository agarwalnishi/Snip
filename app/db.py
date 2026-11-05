from fastapi import Request
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    return create_async_engine(url, pool_size=10, max_overflow=20)


async def get_session(request: Request):
    async with request.app.state.sessionmaker() as session:
        yield session