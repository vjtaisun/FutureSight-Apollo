from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.exceptions import AppError
from app.core.settings import get_settings


class OpenAIClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise AppError("OPENAI_API_KEY is not configured.", status_code=500)
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.request_timeout_seconds,
        )
        self.default_model = settings.openai_model

    async def responses_create(self, **kwargs):  # type: ignore[no-untyped-def]
        return await self.client.responses.create(**kwargs)

    async def responses_create_stream(self, **kwargs) -> AsyncGenerator[object, None]:  # type: ignore[no-untyped-def]
        stream = await self.client.responses.create(**kwargs)
        async for event in stream:
            yield event


_openai_client: OpenAIClient | None = None


def get_openai_client() -> OpenAIClient:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
