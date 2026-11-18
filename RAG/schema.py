from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    doc_id: str | None = None          


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    pages: list[int]                   