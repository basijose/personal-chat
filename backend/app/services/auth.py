from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    AuthenticatedIdentity,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User


COOKIE_NAME = "personal_chat_access_token"


@dataclass(slots=True)
class AuthResult:
    user: User
    token: str


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    stmt = select(User).where(or_(User.username == identifier, User.email == identifier))
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not user.active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def issue_login_cookie(user: User) -> tuple[str, str]:
    settings = get_settings()
    token = create_access_token(
        subject=str(user.id),
        secret=settings.jwt_secret,
        expires_minutes=settings.jwt_access_token_expire_minutes,
        claims={
            "organization_id": user.organization_id,
            "is_superadmin": user.is_superadmin,
        },
    )
    return COOKIE_NAME, token


def read_identity_from_request(request: Request) -> AuthenticatedIdentity:
    settings = get_settings()
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(token, settings.jwt_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    return AuthenticatedIdentity(
        user_id=int(payload["sub"]),
        organization_id=int(payload["organization_id"]),
        is_superadmin=bool(payload.get("is_superadmin", False)),
    )


def logout_cookie() -> tuple[str, str]:
    return COOKIE_NAME, ""


def password_hash_for_seed(password: str) -> str:
    return hash_password(password)

