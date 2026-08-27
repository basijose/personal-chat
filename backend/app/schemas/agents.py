from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RolePublic(BaseModel):
    id: int
    name: str
    description: str = ""


class ToolPublic(BaseModel):
    id: int
    name: str
    slug: str
    description: str = ""
    tool_type: str
    active: bool
    configuration: dict = Field(default_factory=dict)


class AgentPublic(BaseModel):
    id: int
    name: str
    slug: str
    description: str = ""
    provider: str
    model: str
    temperature: float
    active: bool
    tool_count: int = 0
    role_count: int = 0
    roles: list[str] = Field(default_factory=list)


class AgentDetail(AgentPublic):
    system_prompt: str
    tools: list[ToolPublic] = Field(default_factory=list)
    roles: list[RolePublic] = Field(default_factory=list)


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=120)
    description: str = ""
    system_prompt: str = ""
    provider: str = "mock"
    model: str = "mock"
    temperature: float = 0.2
    active: bool = True


class AgentUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    active: bool | None = None


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=120)
    description: str = ""
    tool_type: str = "mock"
    configuration: dict = Field(default_factory=dict)
    active: bool = True


class ToolUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    tool_type: str | None = None
    configuration: dict | None = None
    active: bool | None = None


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class UserCreate(BaseModel):
    organization_id: int | None = None
    username: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    first_name: str = ""
    last_name: str = ""
    active: bool = True
    is_superadmin: bool = False
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    active: bool | None = None
    is_superadmin: bool | None = None
    role_ids: list[int] | None = None


class UserAdminPublic(BaseModel):
    id: int
    organization_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    active: bool
    is_superadmin: bool
    roles: list[str] = Field(default_factory=list)


class ConversationPublic(BaseModel):
    id: int
    organization_id: int
    user_id: int
    agent_id: int
    title: str
    archived: bool = False
    created_at: datetime | None = None


class MessagePublic(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime | None = None


class ConversationAdminPublic(BaseModel):
    id: int
    organization_id: int
    user_id: int
    user_username: str
    agent_id: int
    agent_name: str
    title: str
    archived: bool = False
    message_count: int = 0
    created_at: datetime | None = None


class ConversationArchiveUpdate(BaseModel):
    archived: bool
