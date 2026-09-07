from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    access_token_expires_in: int
    refresh_token_expires_in: int
    jwt_secret: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# lru cache
@lru_cache
def get_settings() -> Settings:
    return Settings()
