import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import cache
from app.clicks import record_click
from app.ratelimit import rate_limit
from app.base62 import random_code
from app.config import settings
from app.db import get_session
from app.models import Link
from app.schemas import ShortenRequest, ShortenResponse

router = APIRouter()
RESERVED = {"health", "docs", "redoc", "openapi.json", "shorten", "stats"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def to_response(link: Link) -> ShortenResponse:
    return ShortenResponse(
        code=link.code,
        short_url=f"{settings.base_url}/{link.code}",
        long_url=link.long_url,
        expires_at=link.expires_at,
    )


@router.post("/shorten", response_model=ShortenResponse, status_code=201,
             dependencies=[Depends(rate_limit)])
async def shorten(body: ShortenRequest, request: Request, response: Response,
                  session: AsyncSession = Depends(get_session)):
    r = request.app.state.redis
    long_url = str(body.url)
    expires_at = now() + timedelta(minutes=body.expires_in_minutes) if body.expires_in_minutes else None

    # custom alias: the user picked the code
    if body.alias:
        if body.alias.lower() in RESERVED:
            raise HTTPException(400, "alias is reserved")
        link = Link(code=body.alias, long_url=long_url, is_custom=True, expires_at=expires_at)
        session.add(link)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(409, "alias already taken")
        await cache.invalidate(r, link.code)
        return to_response(link)

    h = url_hash(long_url)

    # seen this URL before? only for permanent links
    if expires_at is None:
        existing = await session.scalar(
            select(Link).where(Link.url_hash == h, Link.is_custom.is_(False), Link.expires_at.is_(None))
        )
        if existing:
            response.status_code = 200
            return to_response(existing)

    for _ in range(5):
        link = Link(code=random_code(), long_url=long_url, url_hash=h, expires_at=expires_at)
        session.add(link)
        try:
            await session.commit()
            await cache.invalidate(r, link.code)
            return to_response(link)
        except IntegrityError:
            await session.rollback()

    raise HTTPException(500, "could not allocate a code")


@router.get("/{code}")
async def redirect(code: str, request: Request, session: AsyncSession = Depends(get_session)):
    r = request.app.state.redis

    # 1. try the cache first
    if settings.cache_enabled:
        cached = await cache.get(r, code)
        if cached == cache.MISSING:
            raise HTTPException(404, "not found")
        if cached is not None:
            await record_click(r, code)
            return RedirectResponse(cached, status_code=302)

    # 2. cache miss: ask Postgres
    link = await session.scalar(select(Link).where(Link.code == code))
    if link is None:
        if settings.cache_enabled:
            await cache.set_missing(r, code, settings.negative_ttl)
        raise HTTPException(404, "not found")
    if link.expires_at and link.expires_at <= now():
        raise HTTPException(410, "link expired")

    # 3. remember the answer for next time
    if settings.cache_enabled:
        await cache.set_link(r, code, link.long_url, link.expires_at, settings.cache_ttl)
    await record_click(r, code)
    return RedirectResponse(link.long_url, status_code=302)



@router.get("/stats/{code}")
async def stats(code: str, request: Request, session: AsyncSession = Depends(get_session)):
    link = await session.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(404, "not found")
    pending = await request.app.state.redis.hget("clicks:pending", code)
    return {
        "code": code,
        "long_url": link.long_url,
        "clicks": link.clicks + int(pending or 0),
        "created_at": link.created_at,
    }