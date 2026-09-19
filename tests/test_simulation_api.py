from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import create_app


def build_client(database_path: Path) -> TestClient:
    return TestClient(
        create_app(database_url=f"sqlite:///{database_path.as_posix()}")
    )


def create_simulation(client: TestClient) -> dict:
    response = client.post("/api/simulations", json={"aircraft_id": 1})
    assert response.status_code == 201
    return response.json()


def test_simulation_create_and_command_endpoints(tmp_path: Path) -> None:
    with build_client(tmp_path / "simulation-commands.db") as client:
        created = create_simulation(client)
        simulation_id = created["id"]

        assert created["status"] == "STOPPED"
        assert created["telemetry"]["flight_mode"] == "IDLE"
        assert created["telemetry"]["armed"] is False

        started = client.post(f"/api/simulations/{simulation_id}/start")
        assert started.status_code == 200
        assert started.json()["status"] == "RUNNING"

        armed = client.post(f"/api/simulations/{simulation_id}/arm")
        assert armed.status_code == 200
        assert armed.json()["telemetry"]["armed"] is True
        assert armed.json()["telemetry"]["flight_mode"] == "ARMED"

        takeoff = client.post(
            f"/api/simulations/{simulation_id}/takeoff",
            json={"altitude_m": 10.0},
        )
        assert takeoff.status_code == 200
        assert takeoff.json()["telemetry"]["flight_mode"] == "TAKING_OFF"

        wind = client.post(
            f"/api/simulations/{simulation_id}/wind",
            json={"speed_mps": 5.0, "direction_deg": 90.0},
        )
        assert wind.status_code == 200
        assert wind.json()["telemetry"]["wind"] == {
            "speed_mps": 5.0,
            "direction_deg": 90.0,
        }

        paused = client.post(f"/api/simulations/{simulation_id}/pause")
        assert paused.status_code == 200
        assert paused.json()["status"] == "PAUSED"

        reset = client.post(f"/api/simulations/{simulation_id}/reset")
        assert reset.status_code == 200
        assert reset.json()["status"] == "STOPPED"
        assert reset.json()["telemetry"]["t"] == 0.0
        assert reset.json()["telemetry"]["position"]["z"] == 0.0


def test_simulation_rejects_arm_before_start(tmp_path: Path) -> None:
    with build_client(tmp_path / "simulation-errors.db") as client:
        simulation = create_simulation(client)
        response = client.post(f"/api/simulations/{simulation['id']}/arm")

    assert response.status_code == 409


def test_only_one_active_simulation_is_kept(tmp_path: Path) -> None:
    with build_client(tmp_path / "single-simulation.db") as client:
        first = create_simulation(client)
        second = create_simulation(client)

        first_response = client.get(f"/api/simulations/{first['id']}")
        second_response = client.get(f"/api/simulations/{second['id']}")

    assert first_response.status_code == 404
    assert second_response.status_code == 200


def test_websocket_emits_frozen_telemetry_frame(tmp_path: Path) -> None:
    with build_client(tmp_path / "simulation-websocket.db") as client:
        simulation = create_simulation(client)
        simulation_id = simulation["id"]
        client.post(f"/api/simulations/{simulation_id}/start")

        with client.websocket_connect(
            f"/ws/simulations/{simulation_id}"
        ) as websocket:
            frame = websocket.receive_json()

    assert set(frame) == {
        "t",
        "position",
        "velocity",
        "attitude",
        "angular_velocity",
        "center_of_gravity",
        "motors",
        "forces",
        "wind",
        "power",
        "armed",
        "flight_mode",
    }
    assert set(frame["motors"]) == {"outputs", "thrusts_n"}
    assert len(frame["motors"]["outputs"]) == 4
    assert len(frame["motors"]["thrusts_n"]) == 4
