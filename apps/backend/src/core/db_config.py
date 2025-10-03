"""Database configuration utilities for constructing database URLs."""

import os
from typing import Optional
from dotenv import load_dotenv

# Optional override that points the backend at a remote database. When provided, the
# backend skips composing URLs from individual components and simply reuses this value.
BACKEND_DATABASE_URL_ENV = "BACKEND_DATABASE_URL"

# Load environment variables
load_dotenv()


def is_docker_environment() -> bool:
    """Check if running in Docker environment."""
    return os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true'


def _get_database_url_override(driver: str) -> Optional[str]:
    """Return an override URL from BACKEND_DATABASE_URL for the requested driver."""
    override = os.getenv(BACKEND_DATABASE_URL_ENV)
    if not override:
        return None

    # Allow callers to supply driver-specific URLs (e.g., postgresql+asyncpg://...).
    if override.startswith(f"{driver}://"):
        return override

    # Smoothly convert between sync and async Postgres drivers so a single override works.
    if driver == "postgresql+asyncpg" and override.startswith("postgresql://"):
        return override.replace("postgresql://", "postgresql+asyncpg://", 1)

    if driver == "postgresql" and override.startswith("postgresql+asyncpg://"):
        return override.replace("postgresql+asyncpg://", "postgresql://", 1)

    # Fallback: return the override unchanged so custom schemes continue to work.
    return override


def construct_database_url(
    driver: str = "postgresql",
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    database: Optional[str] = None,
    is_docker: Optional[bool] = None
) -> str:
    """
    Construct a database URL from individual components.
    
    Args:
        driver: Database driver (e.g., "postgresql", "postgresql+asyncpg")
        user: Database username
        password: Database password
        host: Database host
        port: Database port
        database: Database name
        is_docker: Whether running in Docker (auto-detected if None)
    
    Returns:
        Constructed database URL
    """
    if is_docker is None:
        is_docker = is_docker_environment()
    
    # Get components from environment if not provided
    if user is None:
        user = os.getenv("BACKEND_POSTGRES_USER", "postgres")
    
    if password is None:
        password = os.getenv("BACKEND_POSTGRES_PASSWORD")
        if not password:
            raise ValueError("BACKEND_POSTGRES_PASSWORD environment variable is not set")
    
    if host is None:
        host_key = "BACKEND_POSTGRES_HOST_DOCKER" if is_docker else "BACKEND_POSTGRES_HOST_LOCAL"
        host = os.getenv(host_key)
        if not host:
            raise ValueError(f"{host_key} environment variable is not set")
    
    if port is None:
        port_key = "BACKEND_POSTGRES_PORT_DOCKER" if is_docker else "BACKEND_POSTGRES_PORT_LOCAL"
        port = os.getenv(port_key)
        if not port:
            raise ValueError(f"{port_key} environment variable is not set")
    
    if database is None:
        database = os.getenv("BACKEND_POSTGRES_DB", "resume_genius")
    
    return f"{driver}://{user}:{password}@{host}:{port}/{database}"


def get_async_database_url(is_docker: Optional[bool] = None) -> str:
    """Get the async database URL for the application."""
    override = _get_database_url_override(driver="postgresql+asyncpg")
    if override:
        return override

    return construct_database_url(
        driver="postgresql+asyncpg",
        is_docker=is_docker
    )


def get_sync_database_url(is_docker: Optional[bool] = None) -> str:
    """Get the sync database URL for migrations."""
    override = _get_database_url_override(driver="postgresql")
    if override:
        return override

    return construct_database_url(
        driver="postgresql",
        is_docker=is_docker
    )


def get_redis_url(is_docker: Optional[bool] = None) -> str:
    """
    Get the Redis URL based on environment.
    
    Args:
        is_docker: Whether running in Docker (auto-detected if None)
    
    Returns:
        Redis URL
    """
    if is_docker is None:
        is_docker = is_docker_environment()
    
    if is_docker:
        host = os.getenv("BACKEND_REDIS_HOST_DOCKER", "resume-genius-redis")
        port = os.getenv("BACKEND_REDIS_PORT_DOCKER", "6379")
    else:
        host = os.getenv("BACKEND_REDIS_HOST_LOCAL", "localhost")
        port = os.getenv("BACKEND_REDIS_PORT_LOCAL", "6380")
    
    database = os.getenv("BACKEND_REDIS_DB", "0")
    return f"redis://{host}:{port}/{database}"
