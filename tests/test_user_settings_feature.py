from __future__ import annotations

from sqlalchemy.orm import Session

from backend.database import build_engine, build_session_factory
from backend.models import Base, UserRecord
from backend.user_settings import (
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
    UserSettings,
    change_password,
    ensure_admin_user,
    hash_password,
    read_settings,
    verify_password,
    write_settings,
)


def memory_session() -> tuple[object, Session]:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = build_session_factory(engine)()
    return engine, session


def test_password_is_hashed_and_verifiable() -> None:
    encoded = hash_password("123456", salt=b"0123456789abcdef")
    assert encoded != "123456"
    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_password("123456", encoded) is True
    assert verify_password("bad-password", encoded) is False


def test_admin_user_is_seeded_with_default_password_and_settings() -> None:
    engine, session = memory_session()
    try:
        record = ensure_admin_user(session)
        assert record.username == DEFAULT_USERNAME
        assert record.password_hash != DEFAULT_PASSWORD
        assert verify_password(DEFAULT_PASSWORD, record.password_hash)
        settings = UserSettings.model_validate(record.settings_json)
        assert settings.general.default_page == "assembly"
        assert settings.display_3d.quality == "balanced"
        assert settings.flight.default_view == "split"
    finally:
        session.close()
        engine.dispose()


def test_settings_update_persists_and_merges_defaults() -> None:
    engine, session = memory_session()
    try:
        ensure_admin_user(session)
        settings = read_settings(session)
        settings.general.decimal_places = 3
        settings.display_3d.show_grid = False
        settings.flight.default_altitude_m = 8.0
        settings.flight.default_view = "3d"
        write_settings(session, settings)

        reloaded = read_settings(session)
        assert reloaded.general.decimal_places == 3
        assert reloaded.display_3d.show_grid is False
        assert reloaded.flight.default_altitude_m == 8.0
        assert reloaded.flight.default_view == "3d"
        # Unedited defaults must survive a round trip.
        assert reloaded.display_3d.show_cg is True
        assert reloaded.flight.auto_connect_telemetry is True
    finally:
        session.close()
        engine.dispose()


def test_password_change_rejects_wrong_current_and_invalidates_old_password() -> None:
    engine, session = memory_session()
    try:
        record = ensure_admin_user(session)
        old_hash = record.password_hash

        try:
            change_password(session, "wrong", "654321")
        except ValueError as error:
            assert "当前密码" in str(error)
        else:
            raise AssertionError("wrong current password should fail")

        change_password(session, DEFAULT_PASSWORD, "654321")
        refreshed = session.get(UserRecord, record.id)
        assert refreshed is not None
        assert refreshed.password_hash != old_hash
        assert verify_password(DEFAULT_PASSWORD, refreshed.password_hash) is False
        assert verify_password("654321", refreshed.password_hash) is True
    finally:
        session.close()
        engine.dispose()
