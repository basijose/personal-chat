from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UserPublic(BaseModel):
    id: int
    organization_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    active: bool
    is_superadmin: bool
    roles: list[str] = []


class LoginResponse(BaseModel):
    user: UserPublic


class MeResponse(BaseModel):
    user: UserPublic
