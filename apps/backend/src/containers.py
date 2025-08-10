from dependency_injector import containers, providers
from openai import OpenAI, AsyncOpenAI


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
