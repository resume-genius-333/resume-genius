from dependency_injector.wiring import inject, Provide
from dotenv import load_dotenv
from src.containers import Container
from openai import OpenAI
import os

@inject
def main(openai: OpenAI = Provide[Container.openai]) -> None:
    # TODO: Implement main functionality
    _ = openai  # Will be used when implementing main logic


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

    # Wire dependencies
    container.wire(modules=[__name__])

    # Run main
    main()
