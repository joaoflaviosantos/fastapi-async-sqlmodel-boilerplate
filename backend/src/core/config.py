# Built-in Dependencies
from typing import Any, List, Union
from enum import Enum
import os

# Third-Party Dependencies
from pydantic_core.core_schema import ValidationInfo
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from starlette.config import Config

# Local Dependencies
from src.core.common.enums import EmailSenderType

# Environment Variables Config Getters
current_file_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.abspath(os.path.join(current_file_dir, "..", "..", ".env"))
config = Config(env_path)


class AppSettings(BaseSettings):
    PROJECT_NAME: str = config("PROJECT_NAME", default="FastAPI Async SQLModel Boilerplate")
    PROJECT_DESCRIPTION: str | None = config("PROJECT_DESCRIPTION", default=None)
    APP_VERSION: str | None = config("APP_VERSION", default="0.0.1")
    LICENSE_NAME: str | None = config("LICENSE_NAME", default=None)
    CONTACT_NAME: str | None = config("CONTACT_NAME", default=None)
    CONTACT_EMAIL: str | None = config("CONTACT_EMAIL", default=None)


class CryptSettings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7)


class EmailSettings(BaseSettings):
    SMTP_HOST: str | None = config("SMTP_HOST", default=None)
    SMTP_PORT: int | None = config("SMTP_PORT", default=587)
    SMTP_USER: str | None = config("SMTP_USER", default=None)
    SMTP_PASSWORD: str | None = config("SMTP_PASSWORD", default=None)
    EMAILS_FROM_EMAIL: str | None = config("EMAILS_FROM_EMAIL", default=None)
    EMAILS_FROM_NAME: str | None = config("EMAILS_FROM_NAME", default=None)
    EMAIL_SENDER: EmailSenderType | str = config("EMAIL_SENDER", default=None)

    @field_validator(
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "EMAILS_FROM_EMAIL",
        "EMAILS_FROM_NAME",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """Convert empty strings to None for optional fields."""
        if v == "":
            return None
        return v

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def empty_str_to_default_port(cls, v: str | int | None) -> int:
        """Convert empty strings to default port 587."""
        if v == "" or v is None:
            return 587
        return int(v)

    @field_validator("EMAIL_SENDER", mode="after")
    def assemble_email_sender(cls, v: str | None, info: ValidationInfo) -> Any:
        # Se o usuário explicitamente definiu "logger", usar logger
        if v == EmailSenderType.logger or v == "logger":
            return EmailSenderType.logger

        # Se o usuário quer smtp, verificar se as credenciais estão configuradas
        if isinstance(v, str) and v != "smtp":
            # Valor vazio ou não reconhecido, verificar credenciais
            if (
                info.data["SMTP_HOST"] == None
                or info.data["SMTP_USER"] == None
                or info.data["SMTP_PASSWORD"] == None
                or info.data["EMAILS_FROM_EMAIL"] == None
                or info.data["EMAILS_FROM_NAME"] == None
            ):
                print(
                    "WARNING: Using logger email sender, because SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAILS_FROM_EMAIL, EMAILS_FROM_NAME are not set"
                )
                return EmailSenderType.logger

        return EmailSenderType.smtp


class PostgresSettings(BaseSettings):
    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="postgres")
    POSTGRES_SERVER: str = config("POSTGRES_SERVER", default="localhost")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", default="postgres")
    POSTGRES_ASYNC_URI: PostgresDsn | str = ""
    POSTGRES_CELERY_URI: str = ""

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

    @field_validator("POSTGRES_CELERY_URI", mode="after")
    def assemble_celery_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                postgres_celery_uri = PostgresDsn.build(
                    scheme="postgresql",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_SERVER"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
                return f"db+{str(postgres_celery_uri)}"
        return v


class FirstTierSettings(BaseSettings):
    TIER_NAME_DEFAULT: str = config("TIER_NAME_DEFAULT", default="Free")


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
    REDIS_CACHE_USERNAME: str = config("REDIS_CACHE_USERNAME", default="")
    REDIS_CACHE_PASSWORD: str = config("REDIS_CACHE_PASSWORD", default="nosecurity")
    REDIS_CACHE_USE_SSL: bool = config("REDIS_CACHE_USE_SSL", default=False)
    REDIS_CACHE_URL: str = (
        f"redis://{REDIS_CACHE_USERNAME}:{REDIS_CACHE_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}"
    )

    @field_validator("REDIS_CACHE_URL", mode="after")
    def assemble_redis_cache_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If SSL is enabled, change the protocol from 'redis://' to 'rediss://' to ensure the connection is encrypted using SSL/TLS.
            if info.data["REDIS_CACHE_USE_SSL"]:
                v = v.replace("redis://", "rediss://")
            # If username and password are not set, use Redis URL connection string without security credentials
            if info.data["REDIS_CACHE_USERNAME"] == "" and info.data["REDIS_CACHE_PASSWORD"] == "":
                return f"redis://{info.data['REDIS_CACHE_HOST']}:{info.data['REDIS_CACHE_PORT']}"
            # If username and password are set, but without security, use Redis URL connection string without password
            if info.data["REDIS_CACHE_PASSWORD"] == "nosecurity":
                return f"redis://{info.data['REDIS_CACHE_USERNAME']}@{info.data['REDIS_CACHE_HOST']}:{info.data['REDIS_CACHE_PORT']}"
        return v


class RedisBrokerSettings(BaseSettings):
    REDIS_BROKER_HOST: str = config("REDIS_BROKER_HOST", default="")
    REDIS_BROKER_PORT: int = config("REDIS_BROKER_PORT", default=6379)
    REDIS_BROKER_USERNAME: str = config("REDIS_BROKER_USERNAME", default="")
    REDIS_BROKER_PASSWORD: str = config("REDIS_BROKER_PASSWORD", default="")
    REDIS_BROKER_USE_SSL: bool = config("REDIS_BROKER_USE_SSL", default=False)
    REDIS_BROKER_URL: str = (
        f"redis://{REDIS_BROKER_USERNAME}:{REDIS_BROKER_PASSWORD}@{REDIS_BROKER_HOST}:{REDIS_BROKER_PORT}"
    )

    @field_validator("REDIS_BROKER_URL", mode="after")
    def assemble_redis_broker_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If SSL is enabled, change the protocol from 'redis://' to 'rediss://' to ensure the connection is encrypted using SSL/TLS.
            if info.data["REDIS_BROKER_USE_SSL"]:
                v = v.replace("redis://", "rediss://")
            # If host is not set, use 'REDIS_CACHE_URL' as Redis Broker URL connection string
            if info.data["REDIS_BROKER_HOST"] == "":
                redis_cache_settings = RedisCacheSettings()
                return redis_cache_settings.REDIS_CACHE_URL
            # If username and password are not set, use Redis URL connection string without security credentials
            if (
                info.data["REDIS_BROKER_USERNAME"] == ""
                and info.data["REDIS_BROKER_PASSWORD"] == ""
            ):
                return f"redis://{info.data['REDIS_BROKER_HOST']}:{info.data['REDIS_BROKER_PORT']}"
            # If username and password are set, but without security, use Redis URL connection string without password
            if info.data["REDIS_BROKER_PASSWORD"] == "nosecurity":
                return f"redis://{info.data['REDIS_BROKER_USERNAME']}@{info.data['REDIS_BROKER_HOST']}:{info.data['REDIS_BROKER_PORT']}"
        return v


class RedisRateLimiterSettings(BaseSettings):
    REDIS_RATE_LIMIT_HOST: str = config("REDIS_RATE_LIMIT_HOST", default="")
    REDIS_RATE_LIMIT_PORT: int = config("REDIS_RATE_LIMIT_PORT", default=6379)
    REDIS_RATE_LIMIT_USERNAME: str = config("REDIS_RATE_LIMIT_USERNAME", default="")
    REDIS_RATE_LIMIT_PASSWORD: str = config("REDIS_RATE_LIMIT_PASSWORD", default="")
    REDIS_RATE_LIMIT_USE_SSL: bool = config("REDIS_RATE_LIMIT_USE_SSL", default=False)
    REDIS_RATE_LIMIT_URL: str = (
        f"redis://{REDIS_RATE_LIMIT_USERNAME}:{REDIS_RATE_LIMIT_PASSWORD}@{REDIS_RATE_LIMIT_HOST}:{REDIS_RATE_LIMIT_PORT}"
    )

    @field_validator("REDIS_RATE_LIMIT_URL", mode="after")
    def assemble_redis_rate_limit_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If SSL is enabled, change the protocol from 'redis://' to 'rediss://' to ensure the connection is encrypted using SSL/TLS.
            if info.data["REDIS_RATE_LIMIT_USE_SSL"]:
                v = v.replace("redis://", "rediss://")
            # If host is not set, use 'REDIS_CACHE_URL' as Redis Queue URL connection string
            if info.data["REDIS_RATE_LIMIT_HOST"] == "":
                redis_cache_settings = RedisCacheSettings()
                return redis_cache_settings.REDIS_CACHE_URL
            # If username and password are not set, use Redis URL connection string without security credentials
            if (
                info.data["REDIS_RATE_LIMIT_USERNAME"] == ""
                and info.data["REDIS_RATE_LIMIT_PASSWORD"] == ""
            ):
                return f"redis://{info.data['REDIS_RATE_LIMIT_HOST']}:{info.data['REDIS_RATE_LIMIT_PORT']}"
            # If username and password are set, but without security, use Redis URL connection string without password
            if info.data["REDIS_RATE_LIMIT_PASSWORD"] == "nosecurity":
                return f"redis://{info.data['REDIS_RATE_LIMIT_USERNAME']}@{info.data['REDIS_RATE_LIMIT_HOST']}:{info.data['REDIS_RATE_LIMIT_PORT']}"
        return v


class RedisHashSettings(BaseSettings):
    REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES: str = "system:auth:valid_usernames"


class DefaultRateLimitSettings(BaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = config("DEFAULT_RATE_LIMIT_LIMIT", default=10)
    DEFAULT_RATE_LIMIT_PERIOD: int = config("DEFAULT_RATE_LIMIT_PERIOD", default=3600)


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = config("CLIENT_CACHE_MAX_AGE", default=60)


class CORSSettings(BaseSettings):
    CORS_ALLOW_ORIGINS: List[str] | str = config("CORS_ALLOW_ORIGINS", default="*").split(",")
    CORS_ALLOW_METHODS: List[str] | str = config("CORS_ALLOW_METHODS", default="*").upper().split(",")  # fmt: skip
    CORS_ALLOW_HEADERS: List[str] | str = config("CORS_ALLOW_HEADERS", default="*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = config("CORS_ALLOW_CREDENTIALS", default="False").lower() == "true"  # fmt: skip
    CORS_EXPOSE_HEADERS: List[str] | str = config("CORS_EXPOSE_HEADERS", default="").split(",")
    CORS_MAX_AGE: int = int(config("CORS_MAX_AGE", default="600"))


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default="local")


class Settings(
    AppSettings,
    EmailSettings,
    PostgresSettings,
    CryptSettings,
    FirstUserSettings,
    FirstTierSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    CORSSettings,
    RedisBrokerSettings,
    RedisRateLimiterSettings,
    RedisHashSettings,
    DefaultRateLimitSettings,
    EnvironmentSettings,
):
    pass


settings = Settings()
