from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    expires_in_minutes: int | None = Field(default=None, gt=0, le=525_600)


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    long_url: str
    expires_at: datetime | None