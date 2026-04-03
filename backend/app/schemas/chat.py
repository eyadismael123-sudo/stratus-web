"""Chat schemas — conversations + messages for client-facing chat."""

from __future__ import annotations

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: str
    client_id: str
    agent_id: str | None = None  # None = Chief of Staff
    created_at: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tokens_used: int | None = None
    created_at: str


class SendMessageRequest(BaseModel):
    content: str


class StartConversationRequest(BaseModel):
    agent_id: str | None = None  # None = Chief of Staff


class ConversationWithMessages(ConversationResponse):
    messages: list[MessageResponse] = []
