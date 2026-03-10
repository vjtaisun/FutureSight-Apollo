from pydantic import BaseModel, Field


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    csv_id: str | None = Field(default=None, min_length=6, max_length=200)
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=700, ge=1, le=4000)
    previous_response_id: str | None = Field(default=None, min_length=6, max_length=200)
