"""Database configuration utilities for constructing database URLs."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def is_docker_environment() -> bool:
    """Check if running in Docker environment."""
    return os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true'


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
    return construct_database_url(
        driver="postgresql+asyncpg",
        is_docker=is_docker
    )


def get_sync_database_url(is_docker: Optional[bool] = None) -> str:
    """Get the sync database URL for migrations."""
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