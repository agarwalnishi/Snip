from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
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


def now() -> datetime:
    return datetime.now(timezone.utc)


def to_response(link: Link) -> ShortenResponse:
    return ShortenResponse(
        code=link.code,
        short_url=f"{settings.base_url}/{link.code}",
        long_url=link.long_url,
        expires_at=link.expires_at,
    )


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten(body: ShortenRequest, session: AsyncSession = Depends(get_session)):
    long_url = str(body.url)

    for _ in range(5):
        link = Link(code=random_code(), long_url=long_url, expires_at=None)
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
    return RedirectResponse(link.long_url, status_code=302)