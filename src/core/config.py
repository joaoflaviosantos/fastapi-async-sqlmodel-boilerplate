# Third-Party Dependencies
from pydantic_core.core_schema import ValidationInfo
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from starlette.config import Config
from typing import Any
from enum import Enum
import os

# Environment Variables Config Getters
current_file_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_file_dir, "..", "..", "..", ".env")
config = Config(env_path)

class AppSettings(BaseSettings):
    PROJECT_NAME: str = config("PROJECT_NAME", default="FastAPI app")
    PROJECT_DESCRIPTION: str | None = config("PROJECT_DESCRIPTION", default=None)
    APP_VERSION: str | None = config("APP_VERSION", default=None)
    LICENSE_NAME: str | None = config("LICENSE", default=None)
    CONTACT_NAME: str | None = config("CONTACT_NAME", default=None)
    CONTACT_EMAIL: str | None = config("CONTACT_EMAIL", default=None)


class CryptSettings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7)


class DatabaseSettings(BaseSettings):
    pass


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="postgres")
    POSTGRES_SERVER: str = config("POSTGRES_SERVER", default="localhost")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", default="postgres")
    POSTGRES_ASYNC_URI: PostgresDsn | str = ""
    
    @field_validator("POSTGRES_ASYNC_URI", mode="after")
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_SERVER"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
        return v


class FirstUserSettings(BaseSettings):
    ADMIN_NAME: str = config("ADMIN_NAME", default="admin")
    ADMIN_EMAIL: str = config("ADMIN_EMAIL", default="admin@admin.com")
    ADMIN_USERNAME: str = config("ADMIN_USERNAME", default="admin")
    ADMIN_PASSWORD: str = config("ADMIN_PASSWORD", default="!Ch4ng3Th1sP4ssW0rd!")


class TestSettings(BaseSettings):
    TEST_NAME: str = config("TEST_NAME", default="Tester User")
    TEST_EMAIL: str = config("TEST_EMAIL", default="test@tester.com")
    TEST_USERNAME: str = config("TEST_USERNAME", default="testeruser")
    TEST_PASSWORD: str = config("TEST_PASSWORD", default="Str1ng$t")


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = config("REDIS_CACHE_HOST", default="localhost")
    REDIS_CACHE_PORT: int = config("REDIS_CACHE_PORT", default=6379)
    REDIS_CACHE_USERNAME: str | None = config("REDIS_CACHE_USERNAME", default=None)
    REDIS_CACHE_PASSWORD: str | None = config("REDIS_CACHE_PASSWORD", default=None)
    REDIS_CACHE_URL: str = f"redis://{REDIS_CACHE_USERNAME}:{REDIS_CACHE_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}"


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = config("CLIENT_CACHE_MAX_AGE", default=60)


class RedisQueueSettings(BaseSettings):
    REDIS_QUEUE_HOST: str = config("REDIS_QUEUE_HOST", default="localhost")
    REDIS_QUEUE_PORT: int = config("REDIS_QUEUE_PORT", default=6379)
    REDIS_QUEUE_USERNAME: str | None = config("REDIS_QUEUE_USERNAME", default=None)
    REDIS_QUEUE_PASSWORD: str | None = config("REDIS_QUEUE_PASSWORD", default=None)
    REDIS_QUEUE_URL: str = f"redis://{REDIS_QUEUE_USERNAME}:{REDIS_QUEUE_PASSWORD}@{REDIS_QUEUE_HOST}:{REDIS_QUEUE_PORT}"

class RedisRateLimiterSettings(BaseSettings):
    REDIS_RATE_LIMIT_HOST: str = config("REDIS_RATE_LIMIT_HOST", default="localhost")
    REDIS_RATE_LIMIT_PORT: int = config("REDIS_RATE_LIMIT_PORT", default=6379)
    REDIS_RATE_LIMIT_USERNAME: str | None = config("REDIS_QUEUE_USERNAME", default=None)
    REDIS_RATE_LIMIT_PASSWORD: str | None = config("REDIS_QUEUE_PASSWORD", default=None)
    REDIS_RATE_LIMIT_URL: str = f"redis://{REDIS_RATE_LIMIT_USERNAME}:{REDIS_RATE_LIMIT_PASSWORD}@{REDIS_RATE_LIMIT_HOST}:{REDIS_RATE_LIMIT_PORT}"


class DefaultRateLimitSettings(BaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = config("DEFAULT_RATE_LIMIT_LIMIT", default=10)
    DEFAULT_RATE_LIMIT_PERIOD: int = config("DEFAULT_RATE_LIMIT_PERIOD", default=3600)


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default="local")


class Settings(
    AppSettings, 
    PostgresSettings, 
    CryptSettings, 
    FirstUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    RedisQueueSettings,
    RedisRateLimiterSettings,
    DefaultRateLimitSettings,
    EnvironmentSettings
):
    pass


settings = Settings()
