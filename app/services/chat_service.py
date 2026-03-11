import json
from collections.abc import AsyncGenerator

from app.core.exceptions import AppError
from app.prompts.system_prompt import get_system_prompt
from app.schemas.chat import ChatStreamRequest
from app.services.openai_client import OpenAIClient, get_openai_client


class ChatService:
    def __init__(
        self,
        client: OpenAIClient | None = None,
    ) -> None:
        self.client = client or get_openai_client()
        self.default_model = self.client.default_model

    @staticmethod
    def _sse(event: str, data: dict[str, object]) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    def _to_responses_input(self, message: str) -> list[dict[str, object]]:
        system_prompt = get_system_prompt()
        items: list[dict[str, object]] = [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            }
        ]

        items.append(
            {
                "role": "user",
                "content": [{"type": "input_text", "text": message}],
            }
        )
        return items

    async def stream_chat(self, payload: ChatStreamRequest) -> AsyncGenerator[str, None]:
        model = payload.model or self.default_model

        request_args: dict[str, object] = {
            "model": model,
            "input": self._to_responses_input(payload.message),
            "temperature": payload.temperature,
            "max_output_tokens": payload.max_output_tokens,
            "stream": True,
        }
        if payload.csv_id:
            request_args["tools"] = [
                {"type": "file_search", "vector_store_ids": [payload.csv_id]}
            ]
        if payload.previous_response_id:
            request_args["previous_response_id"] = payload.previous_response_id

        try:
            async for event in self.client.responses_create_stream(**request_args):
                event_type = getattr(event, "type", "")

                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield self._sse("token", {"text": delta})
                elif event_type == "response.completed":
                    response = getattr(event, "response", None)
                    usage = getattr(response, "usage", None)
                    usage_payload = {
                        "input_tokens": getattr(usage, "input_tokens", None),
                        "output_tokens": getattr(usage, "output_tokens", None),
                        "total_tokens": getattr(usage, "total_tokens", None),
                    }
                    yield self._sse(
                        "done",
                        {
                            "model": model,
                            "usage": usage_payload,
                            "response_id": getattr(response, "id", None),
                        },
                    )
                elif event_type == "error":
                    message = getattr(event, "message", "Upstream model error")
                    yield self._sse("error", {"message": message})

        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Chat streaming failed: {exc}", status_code=502) from exc


_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
