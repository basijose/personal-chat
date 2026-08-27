from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Agent, Conversation, Message, User
from app.schemas.chat import ChatMessageRequest, ChatResponse
from app.services.agent_runtime import run_agent_chat, user_can_use_agent
from app.services.audit import write_audit
from app.services.tool_executors import ToolExecutionError

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatMessageRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChatResponse:
    if len(payload.message) > 4000:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Message too long")
    agent = db.execute(
        select(Agent).where(Agent.id == payload.agent_id, Agent.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not user_can_use_agent(user, agent):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent not permitted")

    if payload.conversation_id:
        conversation = db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == payload.conversation_id,
                Conversation.organization_id == user.organization_id,
                Conversation.user_id == user.id,
                Conversation.archived.is_(False),
            )
        ).scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conversation = Conversation(
            organization_id=user.organization_id,
            user_id=user.id,
            agent_id=agent.id,
            title=payload.message[:64],
        )
        db.add(conversation)
        db.flush()
        write_audit(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            agent_id=agent.id,
            tool_id=None,
            action="conversation_started",
            request_summary=payload.message[:500],
            result_summary=f"conversation_id={conversation.id}",
            status="ok",
        )

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
        metadata_={"agent_id": agent.id},
    )
    db.add(user_message)
    db.flush()
    try:
        result = run_agent_chat(db, user=user, agent=agent, user_message=payload.message, conversation=conversation)
    except ToolExecutionError as exc:
        db.rollback()
        write_audit(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            agent_id=agent.id,
            tool_id=None,
            action="tool_rejected",
            request_summary=payload.message[:1000],
            result_summary=str(exc)[:1000],
            status="denied",
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tool not permitted") from exc
    db.commit()
    return ChatResponse(
        conversation_id=result.conversation.id,
        assistant_message=result.assistant_message.content,
    )
