from __future__ import annotations

from sqlalchemy import select

from backend.auth import (
    AIRCRAFT_LIMIT_PER_USER,
    ensure_legacy_aircraft_ownership,
    session_token_hash,
)
from backend.database import build_engine, build_session_factory
from backend.models import AircraftRecord, Base, UserRecord
from backend.user_settings import ensure_admin_user, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    encoded = hash_password("abcdef")
    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_password("abcdef", encoded) is True
    assert verify_password("wrong-password", encoded) is False


def test_session_token_hash_is_deterministic_and_not_plaintext() -> None:
    token = "example-session-token"
    digest = session_token_hash(token)
    assert digest == session_token_hash(token)
    assert digest != token
    assert len(digest) == 64


def test_legacy_aircraft_is_assigned_to_admin() -> None:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)

    with factory() as session:
        aircraft = AircraftRecord(name="Legacy")
        session.add(aircraft)
        session.commit()
        admin = ensure_admin_user(session)
        changed = ensure_legacy_aircraft_ownership(session, admin)
        assert changed == 1
        record = session.scalar(select(AircraftRecord))
        assert record is not None
        assert record.owner_user_id == admin.id
        assert admin.role == "admin"
        assert admin.is_active == 1

    engine.dispose()


def test_user_profile_fields_support_non_admin_accounts() -> None:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)

    with factory() as session:
        user = UserRecord(
            username="student01",
            password_hash=hash_password("123456"),
            display_name="Student 01",
            role="student",
            is_active=1,
            settings_json={},
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.id > 0
        assert user.role == "student"
        assert AIRCRAFT_LIMIT_PER_USER == 10

    engine.dispose()
