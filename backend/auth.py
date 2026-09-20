from __future__ import annotations

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from backend.models import AircraftRecord, SessionRecord, UserRecord
from backend.user_settings import (
    default_settings_dict,
    hash_password,
    verify_password,
)

SESSION_COOKIE_NAME = "uav_session"
SESSION_TTL_DAYS = 7
AIRCRAFT_LIMIT_PER_USER = 10
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")


class AuthModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(AuthModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(AuthModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: str = Field(default="", max_length=120)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not USERNAME_PATTERN.fullmatch(username):
            raise ValueError("用户名只能包含字母、数字、下划线或连字符，长度 3-32 位")
        return username

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        return value.strip()


class AuthUser(AuthModel):
    id: int
    username: str
    display_name: str
    role: str
    aircraft_limit: int = AIRCRAFT_LIMIT_PER_USER


class AuthSessionResponse(AuthModel):
    user: AuthUser


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def normalize_username(value: str) -> str:
    return value.strip().lower()


def session_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def auth_user(record: UserRecord) -> AuthUser:
    return AuthUser(
        id=record.id,
        username=record.username,
        display_name=(record.display_name or record.username),
        role=(record.role or "student"),
    )


def ensure_user_profile(record: UserRecord, *, admin: bool = False) -> bool:
    changed = False
    if not record.display_name:
        record.display_name = record.username
        changed = True
    expected_role = "admin" if admin else (record.role or "student")
    if record.role != expected_role:
        record.role = expected_role
        changed = True
    if record.is_active is None:
        record.is_active = 1
        changed = True
    if not record.created_at:
        record.created_at = utc_now_iso()
        changed = True
    return changed


def ensure_legacy_aircraft_ownership(session: Session, admin: UserRecord) -> int:
    """Assign pre-auth aircraft to the legacy administrator exactly once."""

    result = session.execute(
        update(AircraftRecord)
        .where(AircraftRecord.owner_user_id.is_(None))
        .values(owner_user_id=admin.id)
    )
    session.commit()
    return int(result.rowcount or 0)


def cleanup_expired_sessions(session: Session) -> None:
    session.execute(
        delete(SessionRecord).where(SessionRecord.expires_at <= utc_now_iso())
    )
    session.commit()


def create_session(session: Session, user: UserRecord) -> tuple[str, SessionRecord]:
    cleanup_expired_sessions(session)
    token = secrets.token_urlsafe(32)
    now = utc_now()
    record = SessionRecord(
        token_hash=session_token_hash(token),
        user_id=user.id,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(days=SESSION_TTL_DAYS)).isoformat(),
        last_seen_at=now.isoformat(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return token, record


def session_user(session: Session, token: str | None) -> UserRecord | None:
    if not token:
        return None
    record = session.scalar(
        select(SessionRecord).where(
            SessionRecord.token_hash == session_token_hash(token)
        )
    )
    if record is None:
        return None
    try:
        expires_at = datetime.fromisoformat(record.expires_at)
    except ValueError:
        session.delete(record)
        session.commit()
        return None
    if expires_at <= utc_now():
        session.delete(record)
        session.commit()
        return None
    user = session.get(UserRecord, record.user_id)
    if user is None or user.is_active == 0:
        session.delete(record)
        session.commit()
        return None

    now = utc_now()
    try:
        last_seen = datetime.fromisoformat(record.last_seen_at)
    except ValueError:
        last_seen = now - timedelta(hours=1)
    if now - last_seen >= timedelta(minutes=5):
        record.last_seen_at = now.isoformat()
        session.commit()
    return user


def request_user(session: Session, request: Request) -> UserRecord | None:
    return session_user(session, request.cookies.get(SESSION_COOKIE_NAME))


def require_current_user(
    request: Request,
    session: Session,
) -> UserRecord:
    user_id = getattr(request.state, "user_id", None)
    if isinstance(user_id, int):
        user = session.get(UserRecord, user_id)
        if user is not None and user.is_active != 0:
            return user
    user = request_user(session, request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    return user


def set_session_cookie(response: Response, token: str) -> None:
    secure = os.getenv("UAV_SESSION_SECURE_COOKIE", "0") == "1"
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        path="/",
    )


def register_auth_routes(
    app: FastAPI,
    get_db: Callable[..., Iterator[Session]],
) -> None:
    @app.post("/api/auth/register", response_model=AuthSessionResponse, status_code=201)
    def register(
        command: RegisterRequest,
        response: Response,
        session: Session = Depends(get_db),
    ) -> AuthSessionResponse:
        username = normalize_username(command.username)
        existing = session.scalar(
            select(UserRecord).where(UserRecord.username == username)
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在",
            )

        user = UserRecord(
            username=username,
            password_hash=hash_password(command.password),
            display_name=command.display_name or username,
            role="student",
            is_active=1,
            created_at=utc_now_iso(),
            settings_json=default_settings_dict(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token, _ = create_session(session, user)
        set_session_cookie(response, token)
        return AuthSessionResponse(user=auth_user(user))

    @app.post("/api/auth/login", response_model=AuthSessionResponse)
    def login(
        command: LoginRequest,
        response: Response,
        session: Session = Depends(get_db),
    ) -> AuthSessionResponse:
        username = normalize_username(command.username)
        user = session.scalar(
            select(UserRecord).where(UserRecord.username == username)
        )
        if (
            user is None
            or user.is_active == 0
            or not verify_password(command.password, user.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码不正确",
            )
        if ensure_user_profile(user, admin=(user.username == "admin")):
            session.commit()
        token, _ = create_session(session, user)
        set_session_cookie(response, token)
        return AuthSessionResponse(user=auth_user(user))

    @app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(
        request: Request,
        response: Response,
        session: Session = Depends(get_db),
    ) -> Response:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            record = session.scalar(
                select(SessionRecord).where(
                    SessionRecord.token_hash == session_token_hash(token)
                )
            )
            if record is not None:
                session.delete(record)
                session.commit()
        clear_session_cookie(response)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @app.get("/api/auth/me", response_model=AuthUser)
    def me(
        request: Request,
        session: Session = Depends(get_db),
    ) -> AuthUser:
        return auth_user(require_current_user(request, session))
