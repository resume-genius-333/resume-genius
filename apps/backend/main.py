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
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Initialize container
    container = Container()

    # Configure container from environment
    # LiteLLM configuration
    container.config.litellm.api_key.from_env("LITELLM_API_KEY", required=True)
    container.config.litellm.base_url.from_env("LITELLM_BASE_URL", required=True)
    
    # Database configuration
    container.config.database.url.from_env("DATABASE_URL", required=True)
    container.config.database.sync_url.from_env("DATABASE_SYNC_URL", required=True)
    container.config.database.echo.from_value(os.getenv("DATABASE_ECHO", "false").lower() == "true")
    
    # Authentication configuration
    container.config.auth.jwt_secret_key.from_env("AUTH_JWT_SECRET_KEY", required=True)
    container.config.auth.jwt_algorithm.from_env("AUTH_JWT_ALGORITHM", default="HS256")
    container.config.auth.access_token_expire_minutes.from_env("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", default="30")
    container.config.auth.refresh_token_expire_days.from_env("AUTH_REFRESH_TOKEN_EXPIRE_DAYS", default="7")
    container.config.auth.password_reset_token_expire_hours.from_env("AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS", default="24")
    container.config.auth.email_verification_token_expire_hours.from_env("AUTH_EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", default="48")

    # Wire dependencies
    container.wire(modules=[__name__, "src.api.dependencies"])

    # Run FastAPI server
    asyncio.run(run_fastapi())
