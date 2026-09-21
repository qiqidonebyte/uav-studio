from __future__ import annotations

import base64
import hashlib
import hmac
import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Callable, Iterator, Literal

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import UserRecord
from backend.teacher_workbench import register_teacher_workbench_routes

PBKDF2_ITERATIONS = 210_000
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "123456"


class MutableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class GeneralSettings(MutableModel):
    unit_system: Literal["metric"] = "metric"
    decimal_places: int = Field(default=2, ge=0, le=4)
    default_page: Literal["assembly", "flight", "history", "components"] = "assembly"
    default_aircraft_id: int = Field(default=1, ge=1)
    confirm_dangerous_actions: bool = True


class Display3DSettings(MutableModel):
    quality: Literal["performance", "balanced", "high"] = "balanced"
    antialias: bool = True
    shadows: Literal["off", "low", "medium", "high"] = "medium"
    environment_reflection: bool = True
    show_grid: bool = True
    show_axes: bool = True
    show_cg: bool = True
    show_thrust_vectors: bool = True
    show_gravity_vector: bool = True
    show_wind_vector: bool = True
    show_trajectory: bool = True
    trajectory_points: int = Field(default=600, ge=100, le=2000)
    default_camera: Literal["free", "follow", "top", "side"] = "free"


class FlightSettings(MutableModel):
    default_altitude_m: float = Field(default=5.0, ge=0.5, le=120.0)
    default_wind_speed_mps: float = Field(default=0.0, ge=0.0, le=30.0)
    default_wind_direction_deg: float = Field(default=90.0, ge=0.0, le=360.0)
    default_view: Literal["3d", "map", "split"] = "split"
    chart_window_seconds: int = Field(default=60, ge=10, le=300)
    max_trajectory_points: int = Field(default=600, ge=100, le=2000)
    auto_create_simulation: bool = False
    auto_connect_telemetry: bool = True
    auto_save_experiment: bool = True


class UserSettings(MutableModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    display_3d: Display3DSettings = Field(default_factory=Display3DSettings)
    flight: FlightSettings = Field(default_factory=FlightSettings)


class UserInfo(MutableModel):
    id: int
    username: str
    display_name: str
    role: str
    aircraft_limit: int = 10


class PasswordChangeRequest(MutableModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def reject_same_password(self) -> "PasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self


class PasswordChangeResult(MutableModel):
    ok: bool = True


def default_settings_dict() -> dict:
    return UserSettings().model_dump(mode="json")


def _urlsafe_no_padding(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_urlsafe(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if len(password) < 6:
        raise ValueError("password must contain at least 6 characters")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{_urlsafe_no_padding(salt)}${_urlsafe_no_padding(digest)}"
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = _decode_urlsafe(salt_text)
        expected = _decode_urlsafe(digest_text)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected),
    )
    return hmac.compare_digest(actual, expected)


def _merge_defaults(defaults: dict, existing: dict | None) -> dict:
    result = deepcopy(defaults)
    if not isinstance(existing, dict):
        return result
    for key, value in existing.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_defaults(result[key], value)
        else:
            result[key] = value
    return result


def ensure_admin_user(session: Session) -> UserRecord:
    record = session.scalar(select(UserRecord).where(UserRecord.username == DEFAULT_USERNAME))
    if record is None:
        record = UserRecord(
            username=DEFAULT_USERNAME,
            password_hash=hash_password(os.getenv("UAV_ADMIN_PASSWORD", DEFAULT_PASSWORD)),
            display_name="Administrator",
            role="admin",
            is_active=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            settings_json=default_settings_dict(),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    changed = False
    merged = _merge_defaults(default_settings_dict(), record.settings_json)
    validated = UserSettings.model_validate(merged).model_dump(mode="json")
    if validated != record.settings_json:
        record.settings_json = validated
        changed = True
    if not record.display_name:
        record.display_name = "Administrator"
        changed = True
    if record.role != "admin":
        record.role = "admin"
        changed = True
    if record.is_active is None:
        record.is_active = 1
        changed = True
    if not record.created_at:
        record.created_at = datetime.now(timezone.utc).isoformat()
        changed = True
    if changed:
        session.commit()
        session.refresh(record)
    return record


def read_settings(record: UserRecord) -> UserSettings:
    merged = _merge_defaults(default_settings_dict(), record.settings_json)
    return UserSettings.model_validate(merged)


def write_settings(
    session: Session,
    record: UserRecord,
    settings: UserSettings,
) -> UserSettings:
    record.settings_json = settings.model_dump(mode="json")
    session.commit()
    session.refresh(record)
    return UserSettings.model_validate(record.settings_json)


def change_password(
    session: Session,
    record: UserRecord,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, record.password_hash):
        raise ValueError("当前密码不正确")
    record.password_hash = hash_password(new_password)
    session.commit()


def register_user_settings_routes(
    app: FastAPI,
    get_db: Callable[..., Iterator[Session]],
    get_current_user: Callable[..., UserRecord],
) -> None:
    @app.get("/api/user/me", response_model=UserInfo)
    def get_user(
        record: UserRecord = Depends(get_current_user),
    ) -> UserInfo:
        return UserInfo(
            id=record.id,
            username=record.username,
            display_name=record.display_name or record.username,
            role=record.role or "student",
        )

    @app.put("/api/user/password", response_model=PasswordChangeResult)
    def update_password(
        command: PasswordChangeRequest,
        session: Session = Depends(get_db),
        record: UserRecord = Depends(get_current_user),
    ) -> PasswordChangeResult:
        try:
            change_password(
                session,
                record,
                command.current_password,
                command.new_password,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        return PasswordChangeResult(ok=True)

    @app.get("/api/settings", response_model=UserSettings)
    def get_settings(
        record: UserRecord = Depends(get_current_user),
    ) -> UserSettings:
        return read_settings(record)

    @app.put("/api/settings", response_model=UserSettings)
    def update_settings(
        settings: UserSettings,
        session: Session = Depends(get_db),
        record: UserRecord = Depends(get_current_user),
    ) -> UserSettings:
        return write_settings(session, record, settings)


    # Teacher Workbench V1: roles, classes, assignments and persistent training records.
    register_teacher_workbench_routes(app, get_db, get_current_user)
