from dependency_injector.wiring import inject, Provide
from dotenv import load_dotenv
from src.containers import Container
from openai import OpenAI

@inject
def main(openai: OpenAI = Provide[OpenAI]) -> None:
    pass


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Initialize container
    container = Container()

    # Configure container from environment
    container.config.litellm.api_key.from_env("LITELLM_API_KEY", required=True)
    container.config.litellm.base_url.from_env("LITELLM_BASE_URL", required=True)

    # Wire dependencies
    container.wire(modules=[__name__])

    # Run main
    main()
