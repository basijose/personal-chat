from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    agent_id: int
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    assistant_message: str


class ConversationCreateRequest(BaseModel):
    agent_id: int
    title: str | None = None

