from __future__ import annotations

from sqlalchemy import inspect, text

from backend.database import build_engine, ensure_schema_compatibility


def test_legacy_user_and_aircraft_tables_receive_auth_columns() -> None:
    engine = build_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE users ("
                "id INTEGER PRIMARY KEY, "
                "username VARCHAR(64) NOT NULL, "
                "password_hash VARCHAR(255) NOT NULL, "
                "settings_json JSON NOT NULL"
                ")"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE aircraft ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR(120) NOT NULL"
                ")"
            )
        )

    ensure_schema_compatibility(engine)
    inspector = inspect(engine)
    user_columns = {item["name"] for item in inspector.get_columns("users")}
    aircraft_columns = {item["name"] for item in inspector.get_columns("aircraft")}

    assert {"display_name", "role", "is_active", "created_at"} <= user_columns
    assert "owner_user_id" in aircraft_columns
    assert {
        "description",
        "created_at",
        "updated_at",
        "assembly_instances_json",
        "propeller_directions_json",
    } <= aircraft_columns
    engine.dispose()
