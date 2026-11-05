from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+asyncpg://snip:snip@localhost:5432/snip"
    redis_url: str = "redis://localhost:6379/0"
    base_url: str = "http://localhost:8000"
    cache_enabled: bool = True
    cache_ttl: int = 3600
    negative_ttl: int = 60
    flush_interval: int = 10
    rate_limit: int = 10


settings = Settings()