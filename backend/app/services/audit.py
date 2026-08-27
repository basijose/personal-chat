from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    organization_id: int | None,
    user_id: int | None,
    agent_id: int | None,
    tool_id: int | None,
    action: str,
    request_summary: str,
    result_summary: str,
    status: str,
) -> AuditLog:
    audit = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        agent_id=agent_id,
        tool_id=tool_id,
        action=action,
        request_summary=request_summary[:5000],
        result_summary=result_summary[:5000],
        status=status,
    )
    db.add(audit)
    db.flush()
    return audit

