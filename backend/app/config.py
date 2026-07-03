from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    refresh_interval_seconds: int = 300
    cors_origins: str = "*"

    github_username: Optional[str] = None
    github_token: Optional[str] = None

    wakatime_api_key: Optional[str] = None

    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    spotify_refresh_token: Optional[str] = None

    strava_client_id: Optional[str] = None
    strava_client_secret: Optional[str] = None
    strava_refresh_token: Optional[str] = None

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
