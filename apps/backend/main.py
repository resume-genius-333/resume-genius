from dependency_injector.wiring import inject, Provide
from dotenv import load_dotenv
from src.containers import Container
from openai import OpenAI
import os
import uvicorn
import asyncio


@inject
def main(openai: OpenAI = Provide[Container.openai]) -> None:
    # TODO: Implement main functionality
    _ = openai  # Will be used when implementing main logic


async def run_fastapi():
    """Run the FastAPI server"""
    config = uvicorn.Config(
        "src.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    os.environ["no_proxy"] = "localhost,127.0.0.1"

    # Initialize container
    container = Container()

    # Configure container from environment
    # LiteLLM configuration
    container.config.litellm.api_key.from_env("LITELLM_API_KEY", required=True)
    container.config.litellm.base_url.from_env("LITELLM_BASE_URL", required=True)

    # Database configuration
    container.config.database.url.from_env("DATABASE_URL", required=True)
    container.config.database.sync_url.from_env("DATABASE_SYNC_URL", required=True)
    container.config.database.echo.from_value(
        os.getenv("DATABASE_ECHO", "false").lower() == "true"
    )

    # Authentication configuration
    container.config.auth.jwt_secret_key.from_env("AUTH_JWT_SECRET_KEY", required=True)
    container.config.auth.jwt_algorithm.from_env("AUTH_JWT_ALGORITHM", default="HS256")
    container.config.auth.access_token_expire_minutes.from_env(
        "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", default="30"
    )
    container.config.auth.refresh_token_expire_days.from_env(
        "AUTH_REFRESH_TOKEN_EXPIRE_DAYS", default="7"
    )
    container.config.auth.password_reset_token_expire_hours.from_env(
        "AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS", default="24"
    )
    container.config.auth.email_verification_token_expire_hours.from_env(
        "AUTH_EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", default="48"
    )

    # Redis configuration
    container.config.redis.url.from_env("REDIS_URL", required=True)
    container.config.redis.max_connections.from_value(
        int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    )
    container.config.redis.encoding.from_env("REDIS_ENCODING", default="utf-8")
    container.config.redis.decode_responses.from_value(
        os.getenv("REDIS_DECODE_RESPONSES", "true").lower() == "true"
    )
    container.config.redis.socket_connect_timeout.from_value(
        int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
    )
    container.config.redis.socket_timeout.from_value(
        int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    )
    container.config.redis.retry_on_timeout.from_value(
        os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
    )
    container.config.redis.health_check_interval.from_value(
        int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))
    )

    # Wire dependencies
    container.wire(modules=[__name__, "src.api.dependencies", "src.api.routers.jobs"])

    # Run FastAPI server
    asyncio.run(run_fastapi())
