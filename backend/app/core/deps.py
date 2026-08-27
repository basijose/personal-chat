from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import AuthenticatedIdentity
from app.db.session import get_db
from app.models import Agent, User
from app.services.auth import read_identity_from_request


def get_current_identity(request: Request) -> AuthenticatedIdentity:
    return read_identity_from_request(request)


def get_current_user(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> User:
    user = db.execute(select(User).where(User.id == identity.user_id)).scalar_one_or_none()
    if not user or user.organization_id != identity.organization_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_agent_access(
    agent_id: int,
    user: User,
    db: Session,
) -> Agent:
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent or agent.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    user_role_ids = {role.id for role in user.roles}
    agent_role_ids = {role.id for role in agent.roles}
    if not user.is_superadmin and not user_role_ids.intersection(agent_role_ids):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent not permitted")
    if not agent.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent inactive")
    return agent
