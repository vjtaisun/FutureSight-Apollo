from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient

from app.main import app
import app.api.v1.routes_chat as routes_chat

client = TestClient(app)


class MockChatService:
    async def stream_chat(self, _payload) -> AsyncGenerator[str, None]:
        yield 'event: token\ndata: {"text": "Hello"}\n\n'
        yield 'event: token\ndata: {"text": " world"}\n\n'
        yield (
            'event: done\n'
            'data: {"model": "gpt-4.1-mini", "usage": {"total_tokens": 10}, "response_id": "resp_123"}\n\n'
        )


def test_chat_stream_success(monkeypatch) -> None:
    monkeypatch.setattr(routes_chat, "get_chat_service", lambda: MockChatService())

    payload = {
        "message": "Say hello",
        "csv_id": "csv_abc123",
        "temperature": 0.2,
        "max_output_tokens": 64,
        "previous_response_id": "resp_abc123",
    }

    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert "event: token" in body
    assert "Hello" in body
    assert "event: done" in body
    assert "response_id" in body


def test_chat_stream_invalid_payload() -> None:
    payload = {"message": ""}
    response = client.post("/api/v1/chat/stream", json=payload)
    assert response.status_code == 422
