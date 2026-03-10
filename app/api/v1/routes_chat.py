from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatStreamRequest
from app.services.chat_service import get_chat_service

router = APIRouter()


@router.post("/chat/stream")
async def stream_chat(payload: ChatStreamRequest) -> StreamingResponse:
    chat_service = get_chat_service()
    return StreamingResponse(
        chat_service.stream_chat(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
