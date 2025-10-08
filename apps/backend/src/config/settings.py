"""Centralised application settings using Pydantic BaseSettings."""

from __future__ import annotations

import logging
from enum import Enum
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Database configuration backed by unified URLs."""

    primary_url: Optional[str]
    docker_url: Optional[str]
    local_url: Optional[str]
    sync_url_override: Optional[str]
    async_url_override: Optional[str]
    echo: bool

    def _base_url(self, *, is_docker: bool) -> Optional[str]:
        if is_docker and self.docker_url:
            return self.docker_url
        if not is_docker and self.local_url:
            return self.local_url
        return self.primary_url

    def _ensure_url(self, url: Optional[str]) -> str:
        if not url:
            raise ValueError("BACKEND_DATABASE_URL environment variable is not set")
        return url

    @staticmethod
    def _ensure_driver(url: str, *, driver: str) -> str:
        if not url.startswith("postgresql"):
            return url

        if driver == "postgresql":
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)

        if driver == "postgresql+asyncpg" and url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return url

    def _resolve(self, *, is_docker: bool, override: Optional[str], driver: str) -> str:
        candidate = override or self._base_url(is_docker=is_docker)
        url = self._ensure_driver(self._ensure_url(candidate), driver=driver)
        return url

    def sync_url(self, *, is_docker: bool) -> str:
        return self._resolve(is_docker=is_docker, override=self.sync_url_override, driver="postgresql")

    def async_url(self, *, is_docker: bool) -> str:
        return self._resolve(is_docker=is_docker, override=self.async_url_override, driver="postgresql+asyncpg")


class RedisConfig(BaseModel):
    """Redis connection configuration."""

    host_docker: str
    host_local: str
    port_docker: str
    port_local: str
    db: str
    max_connections: int
    encoding: str
    decode_responses: bool
    socket_connect_timeout: int
    socket_timeout: int
    retry_on_timeout: bool
    health_check_interval: int

    def url(self, *, is_docker: bool) -> str:
        host = self.host_docker if is_docker else self.host_local
        port = self.port_docker if is_docker else self.port_local
        return f"redis://{host}:{port}/{self.db}"


class AuthConfig(BaseModel):
    """Authentication and token configuration."""

    jwt_secret_key: Optional[str]
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    password_reset_token_expire_hours: int
    email_verification_token_expire_hours: int


class LiteLLMConfig(BaseModel):
    """LiteLLM connectivity settings."""

    api_key: Optional[str]
    base_url_docker: str
    base_url_local: str

    def base_url(self, *, is_docker: bool) -> str:
        return self.base_url_docker if is_docker else self.base_url_local


class LangfuseConfig(BaseModel):
    secret_key: Optional[str]
    public_key: Optional[str]
    host: Optional[str]


class AWSConfig(BaseModel):
    access_key_id: Optional[str]
    secret_access_key: Optional[str]
    region: Optional[str]
    storage_bucket_name: Optional[str]


class ContainerLiteLLMConfig(BaseModel):
    api_key: str
    base_url: str


class ContainerDatabaseConfig(BaseModel):
    url: str
    sync_url: str
    echo: bool


class ContainerAuthConfig(BaseModel):
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    password_reset_token_expire_hours: int
    email_verification_token_expire_hours: int


class ContainerRedisConfig(BaseModel):
    url: str
    max_connections: int
    encoding: str
    decode_responses: bool
    socket_connect_timeout: int
    socket_timeout: int
    retry_on_timeout: bool
    health_check_interval: int


class StatusStreamBackend(str, Enum):
    """Available backends for status streaming."""

    AUTO = "auto"
    REDIS = "redis"
    QUEUE = "queue"


class ContainerStatusStreamConfig(BaseModel):
    backend: str = Field(default=StatusStreamBackend.AUTO.value)


class ContainerConfig(BaseModel):
    litellm: ContainerLiteLLMConfig
    database: ContainerDatabaseConfig
    auth: ContainerAuthConfig
    redis: ContainerRedisConfig | None
    status_stream: ContainerStatusStreamConfig


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=False,
    )

    docker_container: bool = Field(default=False, alias="DOCKER_CONTAINER")

    backend_database_url: Optional[str] = Field(default=None, alias="BACKEND_DATABASE_URL")
    backend_database_url_docker: Optional[str] = Field(default=None, alias="BACKEND_DATABASE_URL_DOCKER")
    backend_database_url_local: Optional[str] = Field(default=None, alias="BACKEND_DATABASE_URL_LOCAL")
    backend_database_sync_url: Optional[str] = Field(default=None, alias="BACKEND_DATABASE_SYNC_URL")
    backend_database_async_url: Optional[str] = Field(default=None, alias="BACKEND_DATABASE_ASYNC_URL")
    backend_database_echo: bool = Field(default=False, alias="BACKEND_DATABASE_ECHO")

    backend_jwt_secret_key: Optional[str] = Field(default=None, alias="BACKEND_JWT_SECRET_KEY")
    backend_jwt_algorithm: str = Field(default="HS256", alias="BACKEND_JWT_ALGORITHM")
    backend_access_token_expire_minutes: int = Field(default=30, alias="BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES")
    backend_refresh_token_expire_days: int = Field(default=7, alias="BACKEND_REFRESH_TOKEN_EXPIRE_DAYS")
    backend_password_reset_token_expire_hours: int = Field(default=24, alias="BACKEND_PASSWORD_RESET_TOKEN_EXPIRE_HOURS")
    backend_email_verification_token_expire_hours: int = Field(default=48, alias="BACKEND_EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS")

    backend_redis_host_docker: str = Field(default="resume-genius-redis", alias="BACKEND_REDIS_HOST_DOCKER")
    backend_redis_host_local: str = Field(default="localhost", alias="BACKEND_REDIS_HOST_LOCAL")
    backend_redis_port_docker: str = Field(default="6379", alias="BACKEND_REDIS_PORT_DOCKER")
    backend_redis_port_local: str = Field(default="6380", alias="BACKEND_REDIS_PORT_LOCAL")
    backend_redis_db: str = Field(default="0", alias="BACKEND_REDIS_DB")
    backend_redis_max_connections: int = Field(default=50, alias="BACKEND_REDIS_MAX_CONNECTIONS")
    backend_redis_encoding: str = Field(default="utf-8", alias="BACKEND_REDIS_ENCODING")
    backend_redis_decode_responses: bool = Field(default=True, alias="BACKEND_REDIS_DECODE_RESPONSES")
    backend_redis_socket_connect_timeout: int = Field(default=5, alias="BACKEND_REDIS_SOCKET_CONNECT_TIMEOUT")
    backend_redis_socket_timeout: int = Field(default=5, alias="BACKEND_REDIS_SOCKET_TIMEOUT")
    backend_redis_retry_on_timeout: bool = Field(default=True, alias="BACKEND_REDIS_RETRY_ON_TIMEOUT")
    backend_redis_health_check_interval: int = Field(default=30, alias="BACKEND_REDIS_HEALTH_CHECK_INTERVAL")
    backend_status_stream_backend: StatusStreamBackend = Field(
        default=StatusStreamBackend.AUTO,
        alias="BACKEND_STATUS_STREAM_BACKEND",
    )

    litellm_api_key: Optional[str] = Field(default=None, alias="LITELLM_API_KEY")
    litellm_base_url_docker: str = Field(default="http://litellm:4000", alias="LITELLM_BASE_URL_DOCKER")
    litellm_base_url_local: str = Field(default="http://localhost:4000", alias="LITELLM_BASE_URL_LOCAL")

    langfuse_secret_key: Optional[str] = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_public_key: Optional[str] = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_host: Optional[str] = Field(default=None, alias="LANGFUSE_HOST")

    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = Field(default=None, alias="AWS_REGION")
    storage_bucket_name: Optional[str] = Field(default=None, alias="STORAGE_BUCKET_NAME")

    @property
    def is_docker(self) -> bool:
        return self.docker_container or Path("/.dockerenv").exists()

    @cached_property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            primary_url=self.backend_database_url,
            docker_url=self.backend_database_url_docker,
            local_url=self.backend_database_url_local,
            sync_url_override=self.backend_database_sync_url,
            async_url_override=self.backend_database_async_url,
            echo=self.backend_database_echo,
        )

    @cached_property
    def redis(self) -> RedisConfig:
        return RedisConfig(
            host_docker=self.backend_redis_host_docker,
            host_local=self.backend_redis_host_local,
            port_docker=self.backend_redis_port_docker,
            port_local=self.backend_redis_port_local,
            db=self.backend_redis_db,
            max_connections=self.backend_redis_max_connections,
            encoding=self.backend_redis_encoding,
            decode_responses=self.backend_redis_decode_responses,
            socket_connect_timeout=self.backend_redis_socket_connect_timeout,
            socket_timeout=self.backend_redis_socket_timeout,
            retry_on_timeout=self.backend_redis_retry_on_timeout,
            health_check_interval=self.backend_redis_health_check_interval,
        )

    def has_redis_config(self) -> bool:
        required_values = [
            self.backend_redis_host_docker,
            self.backend_redis_host_local,
            self.backend_redis_port_docker,
            self.backend_redis_port_local,
            self.backend_redis_db,
        ]
        return all(value not in (None, "") for value in required_values)

    @cached_property
    def auth(self) -> AuthConfig:
        return AuthConfig(
            jwt_secret_key=self.backend_jwt_secret_key,
            jwt_algorithm=self.backend_jwt_algorithm,
            access_token_expire_minutes=self.backend_access_token_expire_minutes,
            refresh_token_expire_days=self.backend_refresh_token_expire_days,
            password_reset_token_expire_hours=self.backend_password_reset_token_expire_hours,
            email_verification_token_expire_hours=self.backend_email_verification_token_expire_hours,
        )

    @cached_property
    def litellm(self) -> LiteLLMConfig:
        return LiteLLMConfig(
            api_key=self.litellm_api_key,
            base_url_docker=self.litellm_base_url_docker,
            base_url_local=self.litellm_base_url_local,
        )

    @cached_property
    def langfuse(self) -> LangfuseConfig:
        return LangfuseConfig(
            secret_key=self.langfuse_secret_key,
            public_key=self.langfuse_public_key,
            host=self.langfuse_host,
        )

    @cached_property
    def aws(self) -> AWSConfig:
        return AWSConfig(
            access_key_id=self.aws_access_key_id,
            secret_access_key=self.aws_secret_access_key,
            region=self.aws_region,
            storage_bucket_name=self.storage_bucket_name,
        )

    def database_url(self, *, driver: str, is_docker: Optional[bool] = None) -> str:
        if is_docker is None:
            is_docker = self.is_docker

        if driver == "postgresql+asyncpg":
            return self.database.async_url(is_docker=is_docker)
        if driver == "postgresql":
            return self.database.sync_url(is_docker=is_docker)

        base = self.database._base_url(is_docker=is_docker)
        return self.database._ensure_url(base)

    def async_database_url(self, is_docker: Optional[bool] = None) -> str:
        if is_docker is None:
            is_docker = self.is_docker
        return self.database.async_url(is_docker=is_docker)

    def sync_database_url(self, is_docker: Optional[bool] = None) -> str:
        if is_docker is None:
            is_docker = self.is_docker
        return self.database.sync_url(is_docker=is_docker)

    def redis_url(self, is_docker: Optional[bool] = None) -> str:
        if is_docker is None:
            is_docker = self.is_docker
        return self.redis.url(is_docker=is_docker)

    def litellm_base_url(self, is_docker: Optional[bool] = None) -> str:
        if is_docker is None:
            is_docker = self.is_docker
        return self.litellm.base_url(is_docker=is_docker)

    def build_container_config(self, *, is_docker: bool) -> ContainerConfig:
        if not self.litellm.api_key:
            raise RuntimeError("LITELLM_API_KEY environment variable must be set")
        if not self.auth.jwt_secret_key:
            raise RuntimeError("BACKEND_JWT_SECRET_KEY environment variable must be set")

        redis_config: ContainerRedisConfig | None = None
        if self.has_redis_config():
            try:
                redis_config = ContainerRedisConfig(
                    url=self.redis.url(is_docker=is_docker),
                    max_connections=self.redis.max_connections,
                    encoding=self.redis.encoding,
                    decode_responses=self.redis.decode_responses,
                    socket_connect_timeout=self.redis.socket_connect_timeout,
                    socket_timeout=self.redis.socket_timeout,
                    retry_on_timeout=self.redis.retry_on_timeout,
                    health_check_interval=self.redis.health_check_interval,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Invalid Redis configuration detected; falling back to queue manager. error=%s",
                    exc,
                )
                redis_config = None

        return ContainerConfig(
            litellm=ContainerLiteLLMConfig(
                api_key=self.litellm.api_key,
                base_url=self.litellm.base_url(is_docker=is_docker),
            ),
            database=ContainerDatabaseConfig(
                url=self.database.async_url(is_docker=is_docker),
                sync_url=self.database.sync_url(is_docker=is_docker),
                echo=self.database.echo,
            ),
            auth=ContainerAuthConfig(
                jwt_secret_key=self.auth.jwt_secret_key,
                jwt_algorithm=self.auth.jwt_algorithm or "HS256",
                access_token_expire_minutes=self.auth.access_token_expire_minutes,
                refresh_token_expire_days=self.auth.refresh_token_expire_days,
                password_reset_token_expire_hours=self.auth.password_reset_token_expire_hours,
                email_verification_token_expire_hours=self.auth.email_verification_token_expire_hours,
            ),
            redis=redis_config,
            status_stream=ContainerStatusStreamConfig(
                backend=self.backend_status_stream_backend.value,
            ),
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


__all__ = [
    "DatabaseConfig",
    "RedisConfig",
    "AuthConfig",
    "LiteLLMConfig",
    "LangfuseConfig",
    "AWSConfig",
    "ContainerConfig",
    "ContainerRedisConfig",
    "ContainerStatusStreamConfig",
    "StatusStreamBackend",
    "Settings",
    "get_settings",
]
