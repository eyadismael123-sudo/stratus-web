"""Chat API — client-facing conversations with agents and Chief of Staff.

Endpoints:
  POST /chat/conversations                  — start a new conversation
  GET  /chat/conversations                  — list all conversations
  GET  /chat/conversations/{id}/messages    — fetch message history
  POST /chat/conversations/{id}/messages    — send a message, get AI reply
"""

from __future__ import annotations

import anthropic
from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.dependencies import get_current_user
from app.exceptions import AppError
from app.repositories import chat as chat_repo
from app.repositories import agents as agent_repo
from app.schemas.chat import (
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse,
    SendMessageRequest,
    StartConversationRequest,
)
from app.schemas.common import SuccessResponse
from app.services.context_builder import build_agent_context, build_cos_context

router = APIRouter(prefix="/chat", tags=["chat"])

_anthropic = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_HAIKU = "claude-haiku-4-5-20251001"
_SONNET = "claude-sonnet-4-6"

# Chief of Staff system prompt
_COS_SYSTEM = (
    "You are the Chief of Staff for this client's AI team on Stratus. "
    "You know everything about their hired agents, their recent activity, "
    "and the signals their agents have discovered. "
    "Answer questions, route requests to the right agent, and help the client "
    "get the most from their team. Be concise and professional."
)


def _agent_system(agent_name: str, role: str) -> str:
    return (
        f"You are {agent_name}, an AI {role} on the Stratus platform. "
        "Use the context below to answer the client's questions in your established voice. "
        "Be concise, specific, and helpful."
    )


@router.post("/conversations", response_model=SuccessResponse[ConversationResponse])
def start_conversation(
    body: StartConversationRequest,
    user: dict = Depends(get_current_user),
) -> SuccessResponse[ConversationResponse]:
    """Start a new conversation. agent_id=None means Chief of Staff."""
    # Validate agent belongs to user if specified
    if body.agent_id:
        agent = agent_repo.get_user_agent(body.agent_id, user["id"])
        if not agent:
            raise AppError(404, "Agent not found")

    conv = chat_repo.create_conversation(user["id"], body.agent_id)
    return SuccessResponse(success=True, data=ConversationResponse(**conv), error=None, error_message=None)


@router.get("/conversations", response_model=SuccessResponse[list[ConversationResponse]])
def list_conversations(
    user: dict = Depends(get_current_user),
) -> SuccessResponse[list[ConversationResponse]]:
    convs = chat_repo.list_conversations(user["id"])
    return SuccessResponse(
        success=True,
        data=[ConversationResponse(**c) for c in convs],
        error=None,
        error_message=None,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=SuccessResponse[ConversationWithMessages],
)
def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
) -> SuccessResponse[ConversationWithMessages]:
    conv = chat_repo.get_conversation(conversation_id, user["id"])
    if not conv:
        raise AppError(404, "Conversation not found")

    messages = chat_repo.list_messages(conversation_id)
    return SuccessResponse(
        success=True,
        data=ConversationWithMessages(
            **conv,
            messages=[MessageResponse(**m) for m in messages],
        ),
        error=None,
        error_message=None,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SuccessResponse[MessageResponse],
)
def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    user: dict = Depends(get_current_user),
) -> SuccessResponse[MessageResponse]:
    """Send a user message and receive an AI reply."""
    conv = chat_repo.get_conversation(conversation_id, user["id"])
    if not conv:
        raise AppError(404, "Conversation not found")

    # Persist user message
    chat_repo.insert_message(conversation_id, "user", body.content)

    # Build context and pick model + system prompt
    is_cos = conv.get("agent_id") is None

    if is_cos:
        context = build_cos_context(user["id"], conversation_id)
        system = f"{_COS_SYSTEM}\n\n{context}" if context else _COS_SYSTEM
        model = _SONNET
    else:
        agent = agent_repo.get_user_agent(conv["agent_id"], user["id"])
        if not agent:
            raise AppError(404, "Agent not found")

        template = agent.get("agent_templates") or {}
        context = build_agent_context(
            client_id=user["id"],
            agent_id=conv["agent_id"],
            industries=template.get("industries", []),
        )
        system = _agent_system(agent["name"], template.get("role", "assistant"))
        if context:
            system = f"{system}\n\n{context}"
        model = _SONNET

    # Fetch recent messages for conversation turns
    history = chat_repo.get_recent_messages(conversation_id, limit=10)
    messages_payload = [
        {"role": m["role"], "content": m["content"]} for m in history
    ]
    # Include the current user message if not already in history
    if not messages_payload or messages_payload[-1]["content"] != body.content:
        messages_payload.append({"role": "user", "content": body.content})

    response = _anthropic.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=messages_payload,
    )

    reply_content = response.content[0].text
    tokens_used = response.usage.output_tokens

    # Persist assistant reply
    saved = chat_repo.insert_message(
        conversation_id, "assistant", reply_content, tokens_used
    )

    return SuccessResponse(
        success=True,
        data=MessageResponse(**saved),
        error=None,
        error_message=None,
    )
