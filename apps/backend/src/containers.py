from typing import TYPE_CHECKING, Optional, Union
from dependency_injector import containers, providers

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import redis.asyncio as redis
from instructor import AsyncInstructor, Instructor, from_openai

from src.services.storage_service import StorageService
from src.core.queue_manager import QueueService
from src.config.settings import ContainerRedisConfig


def _create_redis_client(
    redis_config: Optional[Union[ContainerRedisConfig, dict]],
) -> Optional[redis.Redis]:
    if not redis_config:
        return None

    if isinstance(redis_config, dict):
        # Configuration provider emits plain dicts after model_dump(); normalise to model.
        try:
            redis_config = ContainerRedisConfig(**redis_config)
        except Exception:  # noqa: BLE001
            return None

    return redis.from_url(
        redis_config.url,
        encoding=redis_config.encoding,
        decode_responses=redis_config.decode_responses,
        max_connections=redis_config.max_connections,
        socket_connect_timeout=redis_config.socket_connect_timeout,
        socket_timeout=redis_config.socket_timeout,
        retry_on_timeout=redis_config.retry_on_timeout,
        health_check_interval=redis_config.health_check_interval,
    )

if TYPE_CHECKING:
    from openai import OpenAI, AsyncOpenAI
else:
    from langfuse.openai import OpenAI, AsyncOpenAI


class Container(containers.DeclarativeContainer):
    # Configuration provider
    config = providers.Configuration()

    storage_client = providers.Singleton(StorageService)

    # OpenAI service singleton
    openai_client = providers.Singleton(
        OpenAI,
        api_key=config.litellm.api_key,
        base_url=config.litellm.base_url,
    )

    instructor: providers.Singleton[Instructor] = providers.Singleton(
        from_openai, openai_client
    )

    async_openai = providers.Singleton(
        AsyncOpenAI,
        api_key=config.litellm.api_key,
        base_url=config.litellm.base_url,
    )

    async_instructor: providers.Singleton[AsyncInstructor] = providers.Singleton(
        from_openai, async_openai
    )

    # Database engine (async)
    async_db_engine = providers.Singleton(
        create_async_engine,
        config.database.url,
        echo=config.database.echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Async session factory
    async_session_factory = providers.Singleton(
        async_sessionmaker,
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Sync database engine (for Alembic migrations)
    db_engine = providers.Singleton(
        create_engine,
        config.database.sync_url,
        echo=config.database.echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Sync session factory
    session_factory = providers.Singleton(
        sessionmaker,
        db_engine,
        class_=Session,
        expire_on_commit=False,
    )

    queue_service = providers.Singleton(QueueService)

    # Redis client (async) -- may be None when Redis is not configured
    redis_client = providers.Singleton(
        _create_redis_client,
        config.redis,
    )


# Global container instance
container = Container()
