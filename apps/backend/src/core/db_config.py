"""Database and Redis configuration utilities."""

from __future__ import annotations

from typing import Optional

from src.config.settings import get_settings


def is_docker_environment() -> bool:
    """Return True when the process is running inside Docker."""

    return get_settings().is_docker


def get_async_database_url(is_docker: Optional[bool] = None) -> str:
    """Get the async database URL for the application."""

    settings = get_settings()
    if is_docker is None:
        is_docker = settings.is_docker
    return settings.database.async_url(is_docker=is_docker)


def get_sync_database_url(is_docker: Optional[bool] = None) -> str:
    """Get the sync database URL for migrations."""

    settings = get_settings()
    if is_docker is None:
        is_docker = settings.is_docker
    return settings.database.sync_url(is_docker=is_docker)


def get_redis_url(is_docker: Optional[bool] = None) -> str:
    """Get the Redis URL based on environment."""

    settings = get_settings()
    if is_docker is None:
        is_docker = settings.is_docker

    return settings.redis.url(is_docker=is_docker)
