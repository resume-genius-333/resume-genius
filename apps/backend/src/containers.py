from dependency_injector import containers, providers
from openai import OpenAI, AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class Container(containers.DeclarativeContainer):
    # Configuration provider
    config = providers.Configuration()

    # OpenAI service singleton
    openai = providers.Singleton(
        OpenAI,
        api_key=config.litellm.api_key,
        base_url=config.litellm.base_url,
    )

    async_openai = providers.Singleton(
        AsyncOpenAI,
        api_key=config.litellm.api_key,
        base_url=config.litellm.base_url,
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
