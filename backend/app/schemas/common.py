from __future__ import annotations

from pydantic import BaseModel, Field


class IdResponse(BaseModel):
    id: int


class StatusResponse(BaseModel):
    ok: bool = True


class ErrorResponse(BaseModel):
    detail: str = Field(default="")

