from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@contextmanager
def build_client(database_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(database_url=f"sqlite:///{database_path.as_posix()}")) as client:
        login = client.post("/api/auth/login", json={"username": "admin", "password": os.getenv("UAV_ADMIN_PASSWORD", "123456")})
        assert login.status_code == 200
        yield client


def test_component_catalog_api_returns_seed_components(tmp_path: Path) -> None:
    with build_client(tmp_path / "components.db") as client:
        response = client.get("/api/components")

    assert response.status_code == 200
    components = response.json()
    assert {component["type"] for component in components} >= {
        "frame", "motor", "esc", "propeller", "battery", "power_module",
        "flight_controller", "gnss", "payload",
    }


def test_component_catalog_can_filter_by_type(tmp_path: Path) -> None:
    with build_client(tmp_path / "filter.db") as client:
        response = client.get("/api/components", params={"type": "motor"})
    assert response.status_code == 200
    components = response.json()
    assert components
    assert {component["type"] for component in components} == {"motor"}


def test_default_aircraft_contains_real_engineering_and_validation(tmp_path: Path) -> None:
    with build_client(tmp_path / "aircraft.db") as client:
        response = client.get("/api/aircraft/1")
    assert response.status_code == 200
    state = response.json()
    assert state["aircraft"]["name"] == "EduQuad-650"
    assert state["validation"]["passed"] is True
    assert state["engineering"]["total_mass_kg"] == 2.92
    assert state["engineering"]["max_total_thrust_n"] == 88.0
    assert state["engineering"]["validation"]["passed"] is True


def test_replacing_components_recalculates_and_persists_engineering_data(tmp_path: Path) -> None:
    database_path = tmp_path / "replace.db"
    with build_client(database_path) as client:
        current = client.get("/api/aircraft/1").json()["aircraft"]
        current.update({"motor_id": 11, "propeller_id": 31, "battery_id": 41})
        update_response = client.put("/api/aircraft/1", json=current)
        reload_response = client.get("/api/aircraft/1")
    assert update_response.status_code == 200
    updated_state = update_response.json()
    assert updated_state["validation"]["passed"] is True
    assert updated_state["aircraft"]["motor_id"] == 11
    assert updated_state["engineering"]["total_mass_kg"] == pytest.approx(3.152)
    assert reload_response.status_code == 200
    assert reload_response.json()["aircraft"]["motor_id"] == 11


def test_installing_payload_updates_mass_cg_and_flight_time(tmp_path: Path) -> None:
    with build_client(tmp_path / "payload.db") as client:
        current = client.get("/api/aircraft/1").json()["aircraft"]
        without_payload = current | {"payload_id": None, "payload_position_m": None}
        first = client.put("/api/aircraft/1", json=without_payload).json()
        with_payload = current | {"payload_id": 80, "payload_position_m": {"x": 0.1, "y": 0.0, "z": -0.12}}
        second = client.put("/api/aircraft/1", json=with_payload).json()
    assert first["validation"]["passed"] is True
    assert second["validation"]["passed"] is True
    assert second["engineering"]["total_mass_kg"] > first["engineering"]["total_mass_kg"]
    assert second["engineering"]["center_of_gravity_m"]["x"] > first["engineering"]["center_of_gravity_m"]["x"]
    assert second["engineering"]["estimated_flight_time_min"] < first["engineering"]["estimated_flight_time_min"]


def test_partial_assembly_returns_backend_blocking_errors_and_no_fake_summary(tmp_path: Path) -> None:
    with build_client(tmp_path / "partial.db") as client:
        current = client.get("/api/aircraft/1").json()["aircraft"]
        partial = current | {"motor_id": None}
        update_response = client.put("/api/aircraft/1", json=partial)
        calculate_response = client.post("/api/aircraft/1/calculate")
    assert update_response.status_code == 200
    state = update_response.json()
    assert state["engineering"] is None
    assert state["validation"]["passed"] is False
    assert "REQUIRED_COMPONENT_MISSING" in {issue["code"] for issue in state["validation"]["blocking_errors"]}
    assert calculate_response.status_code == 200
    assert calculate_response.json()["engineering"] is None


def test_wrong_component_type_is_rejected_by_engineering_validation(tmp_path: Path) -> None:
    with build_client(tmp_path / "wrong-type.db") as client:
        current = client.get("/api/aircraft/1").json()["aircraft"]
        invalid = current | {"motor_id": 30}
        response = client.put("/api/aircraft/1", json=invalid)
    assert response.status_code == 200
    state = response.json()
    assert state["engineering"] is None
    assert "COMPONENT_TYPE_MISMATCH" in {issue["code"] for issue in state["validation"]["blocking_errors"]}


def test_unknown_aircraft_returns_not_found(tmp_path: Path) -> None:
    with build_client(tmp_path / "not-found.db") as client:
        response = client.get("/api/aircraft/999")
    assert response.status_code == 404
