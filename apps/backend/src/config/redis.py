"""Redis configuration."""
from pydantic import BaseModel, Field


class RedisConfig(BaseModel):
    """Redis configuration settings."""
    
    # Connection Settings
    url: str = Field(..., description="Redis connection URL")
    max_connections: int = Field(default=50, description="Maximum number of connections in the pool")
    
    # Encoding Settings
    encoding: str = Field(default="utf-8", description="Character encoding for Redis operations")
    decode_responses: bool = Field(default=True, description="Automatically decode responses to strings")
    
    # Timeout Settings
    socket_connect_timeout: int = Field(default=5, description="Socket connection timeout in seconds")
    socket_timeout: int = Field(default=5, description="Socket operation timeout in seconds")
    
    # Retry Settings
    retry_on_timeout: bool = Field(default=True, description="Retry operations on timeout")
    retry_on_error: list = Field(default_factory=list, description="List of errors to retry on")
    
    # Health Check Settings
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    class Config:
        env_prefix = "REDIS_"