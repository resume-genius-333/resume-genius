from typing import TYPE_CHECKING
from dependency_injector import containers, providers

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import redis.asyncio as redis
from instructor import AsyncInstructor, Instructor, from_openai

from src.services.storage_service import StorageService

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

    # Redis client (async)
    redis_client = providers.Singleton(
        redis.from_url,
        config.redis.url,
        encoding=config.redis.encoding,
        decode_responses=config.redis.decode_responses,
        max_connections=config.redis.max_connections,
        socket_connect_timeout=config.redis.socket_connect_timeout,
        socket_timeout=config.redis.socket_timeout,
        retry_on_timeout=config.redis.retry_on_timeout,
        health_check_interval=config.redis.health_check_interval,
    )


# Global container instance
container = Container()
