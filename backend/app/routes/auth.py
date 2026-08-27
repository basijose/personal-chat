from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import AuditLog
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, UserPublic
from app.services.audit import write_audit
from app.services.auth import authenticate_user, issue_login_cookie, logout_cookie
from app.services.crud import user_role_names

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_public(user) -> UserPublic:
    return UserPublic(
        id=user.id,
        organization_id=user.organization_id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        active=user.active,
        is_superadmin=user.is_superadmin,
        roles=user_role_names(user),
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.identifier, payload.password)
    if not user:
        write_audit(
            db,
            organization_id=None,
            user_id=None,
            agent_id=None,
            tool_id=None,
            action="login_failed",
            request_summary=payload.identifier,
            result_summary="invalid_credentials",
            status="error",
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    cookie_name, token = issue_login_cookie(user)
    response.set_cookie(
        cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
        path="/",
    )
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="login_success",
        request_summary=payload.identifier,
        result_summary="login_ok",
        status="ok",
    )
    db.commit()
    return LoginResponse(user=_user_public(user))


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, bool]:
    cookie_name, _ = logout_cookie()
    response.delete_cookie(cookie_name, path="/")
    write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        agent_id=None,
        tool_id=None,
        action="logout",
        request_summary=user.username,
        result_summary="logout_ok",
        status="ok",
    )
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(user=Depends(get_current_user)) -> MeResponse:
    return MeResponse(user=_user_public(user))

