from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    roles: Mapped[list["Role"]] = relationship(back_populates="organization")
    agents: Mapped[list["Agent"]] = relationship(back_populates="organization")
    tools: Mapped[list["Tool"]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "username", name="uq_user_org_username"),
        UniqueConstraint("organization_id", "email", name="uq_user_org_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="users")
    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_role_org_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    organization: Mapped["Organization"] = relationship(back_populates="roles")
    users: Mapped[list["User"]] = relationship(secondary="user_roles", back_populates="roles")
    agents: Mapped[list["Agent"]] = relationship(secondary="agent_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_agent_org_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="mock")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="mock")
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="agents")
    roles: Mapped[list["Role"]] = relationship(secondary="agent_roles", back_populates="agents")
    tools: Mapped[list["Tool"]] = relationship(secondary="agent_tools", back_populates="agents")


class Tool(Base, TimestampMixin):
    __tablename__ = "tools"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_tool_org_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_type: Mapped[str] = mapped_column(String(80), nullable=False, default="mock")
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="tools")
    agents: Mapped[list["Agent"]] = relationship(secondary="agent_tools", back_populates="tools")


class AgentTool(Base):
    __tablename__ = "agent_tools"
    __table_args__ = (UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool"),)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), primary_key=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"), primary_key=True)
    permission_level: Mapped[str] = mapped_column(String(20), nullable=False, default="execute")
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AgentRole(Base):
    __tablename__ = "agent_roles"
    __table_args__ = (UniqueConstraint("agent_id", "role_id", name="uq_agent_role"),)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Nueva conversación")
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"), nullable=True, index=True)
    tool_id: Mapped[int | None] = mapped_column(ForeignKey("tools.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    request_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
