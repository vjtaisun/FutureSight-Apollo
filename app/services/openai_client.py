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

    async def files_create(self, file_path, purpose: str = "assistants"):
        with open(file_path, "rb") as handle:
            return await self.client.files.create(file=handle, purpose=purpose)

    async def files_create_bytes(self, file_bytes: bytes, filename: str, purpose: str = "assistants"):
        from io import BytesIO

        buffer = BytesIO(file_bytes)
        buffer.name = filename
        return await self.client.files.create(file=buffer, purpose=purpose)

    async def files_content(self, file_id: str) -> bytes:
        content = await self.client.files.content(file_id)
        data = getattr(content, "content", None)
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        if hasattr(content, "read"):
            return await content.read()
        return bytes(content)

    async def vector_store_create(self, name: str | None = None, file_ids: list[str] | None = None):
        payload: dict[str, object] = {}
        if name:
            payload["name"] = name
        if file_ids:
            payload["file_ids"] = file_ids
        return await self.client.vector_stores.create(**payload)

    async def vector_store_files_list(self, vector_store_id: str):
        return await self.client.vector_stores.files.list(vector_store_id=vector_store_id)


_openai_client: OpenAIClient | None = None


def get_openai_client() -> OpenAIClient:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
