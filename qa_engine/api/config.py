from pydantic import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str
    version: str
    description: str
    whitelist: list
    es_cloud_id: Optional[str] = None
    es_username: Optional[str] = None
    es_password: Optional[str] = None
    openai_key: Optional[str] = None
    openai_org: Optional[str] = None

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
