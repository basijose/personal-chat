from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Agent, Tool, User
from app.schemas.agents import AgentDetail, AgentPublic, RolePublic, ToolPublic

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _agent_public(agent: Agent, tool_count: int = 0, role_count: int = 0) -> AgentPublic:
    return AgentPublic(
        id=agent.id,
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        provider=agent.provider,
        model=agent.model,
        temperature=agent.temperature,
        active=agent.active,
        tool_count=tool_count,
        role_count=role_count,
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


@router.get("", response_model=list[AgentPublic])
def list_agents(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AgentPublic]:
    agents = db.execute(
        select(Agent)
        .options(selectinload(Agent.roles), selectinload(Agent.tools))
        .where(Agent.organization_id == user.organization_id, Agent.active.is_(True))
        .order_by(Agent.name.asc())
    ).scalars().all()
    allowed: list[AgentPublic] = []
    for agent in agents:
        user_role_ids = {role.id for role in user.roles}
        agent_role_ids = {role.id for role in agent.roles}
        if user.is_superadmin or user_role_ids.intersection(agent_role_ids):
            allowed.append(_agent_public(agent, len(agent.tools), len(agent.roles)))
    return allowed


@router.get("/{agent_id}", response_model=AgentDetail)
def get_agent(agent_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AgentDetail:
    agent = (
        db.execute(
            select(Agent)
            .options(selectinload(Agent.roles), selectinload(Agent.tools))
            .where(Agent.id == agent_id, Agent.organization_id == user.organization_id)
        )
        .scalar_one_or_none()
    )
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    user_role_ids = {role.id for role in user.roles}
    agent_role_ids = {role.id for role in agent.roles}
    if not user.is_superadmin and not user_role_ids.intersection(agent_role_ids):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent not permitted")
    return AgentDetail(
        **_agent_public(agent, len(agent.tools), len(agent.roles)).model_dump(),
        system_prompt=agent.system_prompt,
        tools=[_tool_public(tool) for tool in agent.tools],
        roles=[RolePublic(id=role.id, name=role.name, description=role.description) for role in agent.roles],
    )
