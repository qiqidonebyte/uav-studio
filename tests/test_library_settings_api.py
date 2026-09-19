from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.component_library import register_component_library_routes
from backend.database import build_engine, build_session_factory
from backend.models import Base
from backend.seed import seed_database
from backend.user_settings import ensure_admin_user, register_user_settings_routes


def build_test_app() -> tuple[FastAPI, object]:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        seed_database(session)
        ensure_admin_user(session)

    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    register_user_settings_routes(app, get_db)
    register_component_library_routes(app, get_db)
    return app, engine


def test_settings_api_persists_and_password_change_validates_current_password() -> None:
    app, engine = build_test_app()
    try:
        with TestClient(app) as client:
            me = client.get("/api/user/me")
            assert me.status_code == 200
            assert me.json() == {"username": "admin"}

            settings = client.get("/api/settings")
            assert settings.status_code == 200
            payload = settings.json()
            payload["display_3d"]["show_grid"] = False
            payload["flight"]["default_altitude_m"] = 7.5
            saved = client.put("/api/settings", json=payload)
            assert saved.status_code == 200

            reloaded = client.get("/api/settings").json()
            assert reloaded["display_3d"]["show_grid"] is False
            assert reloaded["flight"]["default_altitude_m"] == 7.5

            wrong = client.put("/api/user/password", json={
                "current_password": "bad",
                "new_password": "654321",
            })
            assert wrong.status_code == 409

            changed = client.put("/api/user/password", json={
                "current_password": "123456",
                "new_password": "654321",
            })
            assert changed.status_code == 200
            assert changed.json()["ok"] is True
    finally:
        engine.dispose()


def test_component_library_api_filters_clones_and_edits() -> None:
    app, engine = build_test_app()
    try:
        with TestClient(app) as client:
            motors = client.get("/api/library/components", params={"type": "motor"})
            assert motors.status_code == 200
            assert len(motors.json()) >= 2

            searched = client.get("/api/library/components", params={"search": "5010"})
            assert searched.status_code == 200
            assert [item["id"] for item in searched.json()] == [10]

            clone = client.post("/api/library/components/10/clone", json={"name": "API Clone 5010"})
            assert clone.status_code == 201
            cloned = clone.json()
            assert cloned["id"] != 10
            assert cloned["visual"]["file"] == "motor_5010_360kv.glb"

            detail = client.get(f"/api/library/components/{cloned['id']}")
            assert detail.status_code == 200
            update_payload = {
                "name": "API Clone 5010 Edited",
                "mass_kg": cloned["mass_kg"],
                "parameters_json": cloned["parameters_json"],
                "notes": "API test",
                "tags": ["测试", "自定义"],
            }
            updated = client.put(f"/api/library/components/{cloned['id']}", json=update_payload)
            assert updated.status_code == 200
            assert updated.json()["name"] == "API Clone 5010 Edited"
            assert updated.json()["library"]["notes"] == "API test"
    finally:
        engine.dispose()
