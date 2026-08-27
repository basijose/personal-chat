from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Agent, AgentRole, AgentTool, Organization, Role, Tool, User, UserRole


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    return db.execute(select(Organization).where(Organization.slug == slug)).scalar_one_or_none()


def get_user_by_identifier(db: Session, identifier: str, organization_id: int | None = None) -> User | None:
    stmt = select(User).where((User.username == identifier) | (User.email == identifier))
    if organization_id is not None:
        stmt = stmt.where(User.organization_id == organization_id)
    return db.execute(stmt).scalar_one_or_none()


def user_role_names(user: User) -> list[str]:
    return [role.name for role in user.roles]


def ensure_default_role(db: Session, organization: Organization, name: str, description: str = "") -> Role:
    role = db.execute(
        select(Role).where(Role.organization_id == organization.id, Role.name == name)
    ).scalar_one_or_none()
    if role:
        return role
    role = Role(organization_id=organization.id, name=name, description=description)
    db.add(role)
    db.flush()
    return role


def ensure_default_agent(db: Session, organization: Organization, **data) -> Agent:
    agent = db.execute(
        select(Agent).where(Agent.organization_id == organization.id, Agent.slug == data["slug"])
    ).scalar_one_or_none()
    if agent:
        return agent
    agent = Agent(organization_id=organization.id, **data)
    db.add(agent)
    db.flush()
    return agent


def ensure_default_tool(db: Session, organization: Organization, **data) -> Tool:
    tool = db.execute(select(Tool).where(Tool.organization_id == organization.id, Tool.slug == data["slug"])).scalar_one_or_none()
    if tool:
        return tool
    tool = Tool(organization_id=organization.id, **data)
    db.add(tool)
    db.flush()
    return tool


def assign_role_to_user(db: Session, user: User, role: Role) -> None:
    exists = db.execute(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    ).scalar_one_or_none()
    if not exists:
        db.add(UserRole(user_id=user.id, role_id=role.id))


def unassign_role_from_user(db: Session, user: User, role: Role) -> None:
    db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).delete(synchronize_session=False)


def assign_role_to_agent(db: Session, agent: Agent, role: Role) -> None:
    exists = db.execute(
        select(AgentRole).where(AgentRole.agent_id == agent.id, AgentRole.role_id == role.id)
    ).scalar_one_or_none()
    if not exists:
        db.add(AgentRole(agent_id=agent.id, role_id=role.id))


def unassign_role_from_agent(db: Session, agent: Agent, role: Role) -> None:
    db.query(AgentRole).filter(AgentRole.agent_id == agent.id, AgentRole.role_id == role.id).delete(synchronize_session=False)


def assign_tool_to_agent(db: Session, agent: Agent, tool: Tool, permission_level: str = "execute") -> None:
    exists = db.execute(
        select(AgentTool).where(AgentTool.agent_id == agent.id, AgentTool.tool_id == tool.id)
    ).scalar_one_or_none()
    if not exists:
        db.add(AgentTool(agent_id=agent.id, tool_id=tool.id, permission_level=permission_level, active=True))


def unassign_tool_from_agent(db: Session, agent: Agent, tool: Tool) -> None:
    db.query(AgentTool).filter(AgentTool.agent_id == agent.id, AgentTool.tool_id == tool.id).delete(synchronize_session=False)


def make_user_password(password: str) -> str:
    return hash_password(password)
