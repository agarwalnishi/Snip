import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten(body: ShortenRequest, response: Response,
                  session: AsyncSession = Depends(get_session)):
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
            return to_response(link)
        except IntegrityError:
            await session.rollback()

    raise HTTPException(500, "could not allocate a code")


@router.get("/{code}")
async def redirect(code: str, session: AsyncSession = Depends(get_session)):
    link = await session.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(404, "not found")
    if link.expires_at and link.expires_at <= now():
        raise HTTPException(410, "link expired")
    return RedirectResponse(link.long_url, status_code=302)