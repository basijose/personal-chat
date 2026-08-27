from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditLogPublic(BaseModel):
    id: int
    organization_id: int | None
    user_id: int | None
    agent_id: int | None
    tool_id: int | None
    action: str
    request_summary: str
    result_summary: str
    status: str
    created_at: datetime | None = None

