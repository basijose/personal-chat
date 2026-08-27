from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import require_admin
from app.db.session import get_db
from app.models import Agent, AgentRole, AgentTool, AuditLog, Conversation, Message, Organization, Role, Tool, User, UserRole
from app.schemas.agents import (
    AgentCreate,
    AgentDetail,
    AgentPublic,
    AgentUpdate,
    ConversationArchiveUpdate,
    ConversationAdminPublic,
    RoleCreate,
    RolePublic,
    RoleUpdate,
    ToolCreate,
    ToolPublic,
    ToolUpdate,
    MessagePublic,
    UserAdminPublic,
    UserCreate,
    UserUpdate,
)
from app.schemas.audit import AuditLogPublic
from app.services.audit import write_audit
from app.services.crud import (
    assign_role_to_agent,
    assign_role_to_user,
    assign_tool_to_agent,
    make_user_password,
    unassign_role_from_agent,
    unassign_role_from_user,
    unassign_tool_from_agent,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _user_public(user: User) -> UserAdminPublic:
    return UserAdminPublic(
        id=user.id,
        organization_id=user.organization_id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        active=user.active,
        is_superadmin=user.is_superadmin,
        roles=[role.name for role in user.roles],
    )


def _agent_public(agent: Agent) -> AgentPublic:
    return AgentPublic(
        id=agent.id,
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        provider=agent.provider,
        model=agent.model,
        temperature=agent.temperature,
        active=agent.active,
        tool_count=len(agent.tools),
        role_count=len(agent.roles),
        roles=[role.name for role in agent.roles],
    )


def _tool_public(tool: Tool) -> ToolPublic:
    return ToolPublic(
        id=tool.id,
        name=tool.name,
        slug=tool.slug,
        description=tool.description,
        tool_type=tool.tool_type,
        active=tool.active,
        configuration=tool.configuration or {},
    )


@router.get("/users", response_model=list[UserAdminPublic])
def list_users(user=Depends(require_admin), db: Session = Depends(get_db)) -> list[UserAdminPublic]:
    users = db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.organization_id == user.organization_id)
        .order_by(User.id.asc())
    ).scalars().all()
    return [_user_public(item) for item in users]


@router.post("/users", response_model=UserAdminPublic)
def create_user(payload: UserCreate, user=Depends(require_admin), db: Session = Depends(get_db)) -> UserAdminPublic:
    organization_id = payload.organization_id or user.organization_id
    new_user = User(
        organization_id=organization_id,
        username=payload.username,
        email=payload.email,
        password_hash=make_user_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        active=payload.active,
        is_superadmin=payload.is_superadmin,
    )
    db.add(new_user)
    db.flush()
    if payload.role_ids:
        roles = db.execute(
            select(Role).where(Role.organization_id == organization_id, Role.id.in_(payload.role_ids))
        ).scalars().all()
        for role in roles:
            assign_role_to_user(db, new_user, role)
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="admin_create_user",
        request_summary=payload.model_dump_json(),
        result_summary=f"user_id={new_user.id}",
        status="ok",
    )
    db.commit()
    return _user_public(new_user)


@router.patch("/users/{user_id}", response_model=UserAdminPublic)
def update_user(user_id: int, payload: UserUpdate, user=Depends(require_admin), db: Session = Depends(get_db)) -> UserAdminPublic:
    target = db.execute(
        select(User).where(User.id == user_id, User.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "role_ids":
            continue
        setattr(target, field, value)
    if payload.role_ids is not None:
        target.roles.clear()
        roles = db.execute(select(Role).where(Role.organization_id == user.organization_id, Role.id.in_(payload.role_ids))).scalars().all()
        for role in roles:
            assign_role_to_user(db, target, role)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="admin_update_user",
        request_summary=payload.model_dump_json(),
        result_summary=f"user_id={target.id}",
        status="ok",
    )
    db.commit()
    return _user_public(target)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    target = db.execute(
        select(User).where(User.id == user_id, User.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    conversation_ids = db.execute(select(Conversation.id).where(Conversation.user_id == target.id)).scalars().all()
    if conversation_ids:
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
        db.query(Conversation).filter(Conversation.id.in_(conversation_ids)).delete(synchronize_session=False)
    db.query(UserRole).filter(UserRole.user_id == target.id).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.user_id == target.id).update({"user_id": None}, synchronize_session=False)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="admin_delete_user",
        request_summary=f"user_id={target.id}",
        result_summary=target.username,
        status="ok",
    )
    db.delete(target)
    db.commit()
    return {"ok": True}


@router.get("/roles", response_model=list[RolePublic])
def list_roles(user=Depends(require_admin), db: Session = Depends(get_db)) -> list[RolePublic]:
    roles = db.execute(select(Role).where(Role.organization_id == user.organization_id).order_by(Role.name.asc())).scalars().all()
    return [RolePublic(id=role.id, name=role.name, description=role.description) for role in roles]


@router.post("/roles", response_model=RolePublic)
def create_role(payload: RoleCreate, user=Depends(require_admin), db: Session = Depends(get_db)) -> RolePublic:
    role = Role(organization_id=user.organization_id, name=payload.name, description=payload.description)
    db.add(role)
    db.commit()
    return RolePublic(id=role.id, name=role.name, description=role.description)


@router.patch("/roles/{role_id}", response_model=RolePublic)
def update_role(role_id: int, payload: RoleUpdate, user=Depends(require_admin), db: Session = Depends(get_db)) -> RolePublic:
    role = db.execute(select(Role).where(Role.id == role_id, Role.organization_id == user.organization_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    return RolePublic(id=role.id, name=role.name, description=role.description)


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    role = db.execute(select(Role).where(Role.id == role_id, Role.organization_id == user.organization_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    db.query(UserRole).filter(UserRole.role_id == role.id).delete(synchronize_session=False)
    db.query(AgentRole).filter(AgentRole.role_id == role.id).delete(synchronize_session=False)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="admin_delete_role",
        request_summary=f"role_id={role.id}",
        result_summary=role.name,
        status="ok",
    )
    db.delete(role)
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/roles/{role_id}")
def assign_role(user_id: int, role_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    target_user = db.execute(select(User).where(User.id == user_id, User.organization_id == user.organization_id)).scalar_one_or_none()
    role = db.execute(select(Role).where(Role.id == role_id, Role.organization_id == user.organization_id)).scalar_one_or_none()
    if not target_user or not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assign_role_to_user(db, target_user, role)
    db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}/roles/{role_id}")
def remove_user_role(user_id: int, role_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    target_user = db.execute(select(User).where(User.id == user_id, User.organization_id == user.organization_id)).scalar_one_or_none()
    role = db.execute(select(Role).where(Role.id == role_id, Role.organization_id == user.organization_id)).scalar_one_or_none()
    if not target_user or not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    unassign_role_from_user(db, target_user, role)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="admin_unassign_user_role",
        request_summary=f"user_id={user_id}, role_id={role_id}",
        result_summary="ok",
        status="ok",
    )
    db.commit()
    return {"ok": True}


@router.get("/agents", response_model=list[AgentPublic])
def list_admin_agents(user=Depends(require_admin), db: Session = Depends(get_db)) -> list[AgentPublic]:
    agents = db.execute(
        select(Agent)
        .options(selectinload(Agent.roles), selectinload(Agent.tools))
        .where(Agent.organization_id == user.organization_id)
        .order_by(Agent.name.asc())
    ).scalars().all()
    return [_agent_public(agent) for agent in agents]


@router.get("/agents/{agent_id}", response_model=AgentDetail)
def get_admin_agent(agent_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> AgentDetail:
    agent = db.execute(
        select(Agent)
        .options(selectinload(Agent.roles), selectinload(Agent.tools))
        .where(Agent.id == agent_id, Agent.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    base_agent = _agent_public(agent).model_dump(exclude={"roles"})
    return AgentDetail(
        **base_agent,
        system_prompt=agent.system_prompt,
        tools=[
            _tool_public(tool)
            for tool in agent.tools
        ],
        roles=[
            RolePublic(id=role.id, name=role.name, description=role.description)
            for role in agent.roles
        ],
    )


@router.post("/agents", response_model=AgentPublic)
def create_agent(payload: AgentCreate, user=Depends(require_admin), db: Session = Depends(get_db)) -> AgentPublic:
    agent = Agent(
        organization_id=user.organization_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        system_prompt=payload.system_prompt,
        provider=payload.provider,
        model=payload.model,
        temperature=payload.temperature,
        active=payload.active,
    )
    db.add(agent)
    db.commit()
    return _agent_public(agent)


@router.patch("/agents/{agent_id}", response_model=AgentPublic)
def update_agent(agent_id: int, payload: AgentUpdate, user=Depends(require_admin), db: Session = Depends(get_db)) -> AgentPublic:
    agent = db.execute(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    db.commit()
    return _agent_public(agent)


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    agent = db.execute(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    conversation_ids = db.execute(select(Conversation.id).where(Conversation.agent_id == agent.id)).scalars().all()
    if conversation_ids:
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
        db.query(Conversation).filter(Conversation.id.in_(conversation_ids)).delete(synchronize_session=False)
    db.query(AgentRole).filter(AgentRole.agent_id == agent.id).delete(synchronize_session=False)
    db.query(AgentTool).filter(AgentTool.agent_id == agent.id).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.agent_id == agent.id).update({"agent_id": None}, synchronize_session=False)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=agent.id,
        tool_id=None,
        action="admin_delete_agent",
        request_summary=f"agent_id={agent.id}",
        result_summary=agent.name,
        status="ok",
    )
    db.delete(agent)
    db.commit()
    return {"ok": True}


@router.post("/agents/{agent_id}/roles/{role_id}")
def assign_agent_role(agent_id: int, role_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    agent = db.execute(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id)).scalar_one_or_none()
    role = db.execute(select(Role).where(Role.id == role_id, Role.organization_id == user.organization_id)).scalar_one_or_none()
    if not agent or not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assign_role_to_agent(db, agent, role)
    db.commit()
    return {"ok": True}


@router.delete("/agents/{agent_id}/roles/{role_id}")
def remove_agent_role(agent_id: int, role_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    agent = db.execute(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id)).scalar_one_or_none()
    role = db.execute(select(Role).where(Role.id == role_id, Role.organization_id == user.organization_id)).scalar_one_or_none()
    if not agent or not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    unassign_role_from_agent(db, agent, role)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=agent.id,
        tool_id=None,
        action="admin_unassign_agent_role",
        request_summary=f"agent_id={agent_id}, role_id={role_id}",
        result_summary="ok",
        status="ok",
    )
    db.commit()
    return {"ok": True}


@router.get("/tools", response_model=list[ToolPublic])
def list_tools(user=Depends(require_admin), db: Session = Depends(get_db)) -> list[ToolPublic]:
    tools = db.execute(select(Tool).where(Tool.organization_id == user.organization_id).order_by(Tool.name.asc())).scalars().all()
    return [_tool_public(tool) for tool in tools]


@router.post("/tools", response_model=ToolPublic)
def create_tool(payload: ToolCreate, user=Depends(require_admin), db: Session = Depends(get_db)) -> ToolPublic:
    tool = Tool(
        organization_id=user.organization_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        tool_type=payload.tool_type,
        configuration=payload.configuration,
        active=payload.active,
    )
    db.add(tool)
    db.commit()
    return _tool_public(tool)


@router.patch("/tools/{tool_id}", response_model=ToolPublic)
def update_tool(tool_id: int, payload: ToolUpdate, user=Depends(require_admin), db: Session = Depends(get_db)) -> ToolPublic:
    tool = db.execute(select(Tool).where(Tool.id == tool_id, Tool.organization_id == user.organization_id)).scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tool, field, value)
    db.commit()
    return _tool_public(tool)


@router.delete("/tools/{tool_id}")
def delete_tool(tool_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    tool = db.execute(select(Tool).where(Tool.id == tool_id, Tool.organization_id == user.organization_id)).scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    db.query(AgentTool).filter(AgentTool.tool_id == tool.id).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.tool_id == tool.id).update({"tool_id": None}, synchronize_session=False)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=tool.id,
        action="admin_delete_tool",
        request_summary=f"tool_id={tool.id}",
        result_summary=tool.name,
        status="ok",
    )
    db.delete(tool)
    db.commit()
    return {"ok": True}


@router.post("/agents/{agent_id}/tools/{tool_id}")
def assign_agent_tool(agent_id: int, tool_id: int, permission_level: str = "execute", user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    agent = db.execute(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id)).scalar_one_or_none()
    tool = db.execute(select(Tool).where(Tool.id == tool_id, Tool.organization_id == user.organization_id)).scalar_one_or_none()
    if not agent or not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assign_tool_to_agent(db, agent, tool, permission_level=permission_level)
    db.commit()
    return {"ok": True}


@router.delete("/agents/{agent_id}/tools/{tool_id}")
def remove_agent_tool(agent_id: int, tool_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    agent = db.execute(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id)).scalar_one_or_none()
    tool = db.execute(select(Tool).where(Tool.id == tool_id, Tool.organization_id == user.organization_id)).scalar_one_or_none()
    if not agent or not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    unassign_tool_from_agent(db, agent, tool)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=agent.id,
        tool_id=tool.id,
        action="admin_unassign_agent_tool",
        request_summary=f"agent_id={agent_id}, tool_id={tool_id}",
        result_summary="ok",
        status="ok",
    )
    db.commit()
    return {"ok": True}


@router.get("/conversations", response_model=list[ConversationAdminPublic])
def list_admin_conversations(user=Depends(require_admin), db: Session = Depends(get_db)) -> list[ConversationAdminPublic]:
    rows = db.execute(
        select(
            Conversation,
            User.username.label("user_username"),
            Agent.name.label("agent_name"),
            func.count(Message.id).label("message_count"),
        )
        .join(User, User.id == Conversation.user_id)
        .join(Agent, Agent.id == Conversation.agent_id)
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.organization_id == user.organization_id)
        .group_by(
            Conversation.id,
            Conversation.organization_id,
            Conversation.user_id,
            Conversation.agent_id,
            Conversation.title,
            Conversation.archived,
            Conversation.created_at,
            Conversation.updated_at,
            User.username,
            Agent.name,
        )
        .order_by(Conversation.created_at.desc())
    ).all()
    return [
        ConversationAdminPublic(
            id=conversation.id,
            organization_id=conversation.organization_id,
            user_id=conversation.user_id,
            user_username=user_username,
            agent_id=conversation.agent_id,
            agent_name=agent_name,
            title=conversation.title,
            archived=conversation.archived,
            message_count=message_count,
            created_at=conversation.created_at,
        )
        for conversation, user_username, agent_name, message_count in rows
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessagePublic])
def get_admin_conversation_messages(
    conversation_id: int,
    user=Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[MessagePublic]:
    conversation = db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id, Conversation.organization_id == user.organization_id)
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


@router.patch("/conversations/{conversation_id}", response_model=ConversationAdminPublic)
def update_admin_conversation(
    conversation_id: int,
    payload: ConversationArchiveUpdate,
    user=Depends(require_admin),
    db: Session = Depends(get_db),
) -> ConversationAdminPublic:
    conversation = db.execute(
        select(Conversation)
        .join(User, User.id == Conversation.user_id)
        .join(Agent, Agent.id == Conversation.agent_id)
        .where(Conversation.id == conversation_id, Conversation.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    conversation.archived = payload.archived
    db.flush()
    user_username = db.execute(select(User.username).where(User.id == conversation.user_id)).scalar_one()
    agent_name = db.execute(select(Agent.name).where(Agent.id == conversation.agent_id)).scalar_one()
    message_count = db.execute(select(func.count(Message.id)).where(Message.conversation_id == conversation.id)).scalar_one()
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=conversation.agent_id,
        tool_id=None,
        action="admin_update_conversation",
        request_summary=payload.model_dump_json(),
        result_summary=f"conversation_id={conversation.id}",
        status="ok",
    )
    db.commit()
    return ConversationAdminPublic(
        id=conversation.id,
        organization_id=conversation.organization_id,
        user_id=conversation.user_id,
        user_username=user_username,
        agent_id=conversation.agent_id,
        agent_name=agent_name,
        title=conversation.title,
        archived=conversation.archived,
        message_count=message_count,
        created_at=conversation.created_at,
    )


@router.delete("/conversations/{conversation_id}")
def delete_admin_conversation(conversation_id: int, user=Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, bool]:
    conversation = db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.organization_id == user.organization_id)
    ).scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.query(Message).filter(Message.conversation_id == conversation.id).delete(synchronize_session=False)
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=conversation.agent_id,
        tool_id=None,
        action="admin_delete_conversation",
        request_summary=f"conversation_id={conversation.id}",
        result_summary=conversation.title,
        status="ok",
    )
    db.delete(conversation)
    db.commit()
    return {"ok": True}


@router.get("/audit", response_model=list[AuditLogPublic])
def list_audit(user=Depends(require_admin), db: Session = Depends(get_db)) -> list[AuditLogPublic]:
    entries = db.execute(
        select(AuditLog)
        .where(AuditLog.organization_id == user.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    ).scalars().all()
    return [
        AuditLogPublic(
            id=item.id,
            organization_id=item.organization_id,
            user_id=item.user_id,
            agent_id=item.agent_id,
            tool_id=item.tool_id,
            action=item.action,
            request_summary=item.request_summary,
            result_summary=item.result_summary,
            status=item.status,
            created_at=item.created_at,
        )
        for item in entries
    ]
