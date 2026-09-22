from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient

from backend.main import create_app


@contextmanager
def build_client(database_path: Path) -> Iterator[TestClient]:
    with TestClient(
        create_app(database_url=f"sqlite:///{database_path.as_posix()}")
    ) as client:
        yield client


def test_register_me_logout_forms_one_http_session_lifecycle(tmp_path: Path) -> None:
    """Protect the browser-facing registration/session contract, not only helpers."""
    with build_client(tmp_path / "auth-lifecycle.db") as client:
        anonymous = client.get("/api/auth/me")
        assert anonymous.status_code == 401

        registered = client.post(
            "/api/auth/register",
            json={
                "username": " Student_01 ",
                "display_name": " 学生一 ",
                "password": "123456",
            },
        )
        assert registered.status_code == 201
        user = registered.json()["user"]
        assert user["id"] > 0
        assert user | {"id": 0} == {
            "id": 0,
            "username": "student_01",
            "display_name": "学生一",
            "role": "student",
            "aircraft_limit": 10,
        }
        cookie = client.cookies.get("uav_session")
        assert cookie

        current = client.get("/api/auth/me")
        assert current.status_code == 200
        assert current.json()["username"] == "student_01"

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 204
        assert client.get("/api/auth/me").status_code == 401


def test_auth_routes_reject_invalid_duplicate_and_wrong_credentials(tmp_path: Path) -> None:
    with build_client(tmp_path / "auth-errors.db") as client:
        invalid = client.post(
            "/api/auth/register",
            json={"username": "中文", "password": "123456"},
        )
        assert invalid.status_code == 422

        first = client.post(
            "/api/auth/register",
            json={"username": "student02", "password": "123456"},
        )
        assert first.status_code == 201
        client.post("/api/auth/logout")

        duplicate = client.post(
            "/api/auth/register",
            json={"username": "STUDENT02", "password": "123456"},
        )
        assert duplicate.status_code == 409

        wrong_password = client.post(
            "/api/auth/login",
            json={"username": "student02", "password": "not-the-password"},
        )
        assert wrong_password.status_code == 401

        restored = client.post(
            "/api/auth/login",
            json={"username": " student02 ", "password": "123456"},
        )
        assert restored.status_code == 200
        assert restored.json()["user"]["role"] == "student"
