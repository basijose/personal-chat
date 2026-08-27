from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Agent, Conversation, Message, User
from app.schemas.agents import ConversationPublic, MessagePublic
from app.schemas.chat import ConversationCreateRequest
from app.services.audit import write_audit
from app.services.agent_runtime import user_can_use_agent

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationPublic])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ConversationPublic]:
    conversations = db.execute(
        select(Conversation)
        .where(Conversation.organization_id == user.organization_id, Conversation.user_id == user.id, Conversation.archived.is_(False))
        .order_by(Conversation.created_at.desc())
    ).scalars().all()
    return [
        ConversationPublic(
            id=conversation.id,
            organization_id=conversation.organization_id,
            user_id=conversation.user_id,
            agent_id=conversation.agent_id,
            title=conversation.title,
            archived=conversation.archived,
            created_at=conversation.created_at,
        )
        for conversation in conversations
    ]


@router.post("", response_model=ConversationPublic)
def create_conversation(
    payload: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationPublic:
    agent = db.execute(
        select(Agent).where(Agent.id == payload.agent_id, Agent.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not user_can_use_agent(user, agent):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent not permitted")
    conversation = Conversation(
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=payload.agent_id,
        title=payload.title or "Nueva conversación",
    )
    db.add(conversation)
    db.flush()
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=payload.agent_id,
        tool_id=None,
        action="conversation_created",
        request_summary=payload.model_dump_json(),
        result_summary=f"conversation_id={conversation.id}",
        status="ok",
    )
    db.commit()
    return ConversationPublic(
        id=conversation.id,
        organization_id=conversation.organization_id,
        user_id=conversation.user_id,
        agent_id=conversation.agent_id,
        title=conversation.title,
        archived=conversation.archived,
        created_at=conversation.created_at,
    )


@router.get("/{conversation_id}/messages", response_model=list[MessagePublic])
def get_messages(conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MessagePublic]:
    conversation = db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.organization_id == user.organization_id,
            Conversation.user_id == user.id,
            Conversation.archived.is_(False),
        )
    ).scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return [
        MessagePublic(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata_ or {},
            created_at=message.created_at,
        )
        for message in conversation.messages
    ]
