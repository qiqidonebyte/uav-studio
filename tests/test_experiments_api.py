from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import create_app


def build_client(database_path: Path, simulations_dir: Path) -> TestClient:
    return TestClient(
        create_app(
            database_url=f"sqlite:///{database_path.as_posix()}",
            simulations_dir=simulations_dir,
        )
    )


def create_started_simulation(client: TestClient) -> int:
    response = client.post("/api/simulations", json={"aircraft_id": 1})
    assert response.status_code == 201
    simulation_id = response.json()["id"]
    assert client.post(f"/api/simulations/{simulation_id}/start").status_code == 200
    assert client.post(f"/api/simulations/{simulation_id}/arm").status_code == 200
    return simulation_id


def test_target_position_and_waypoints_are_published_to_snapshot(
    tmp_path: Path,
) -> None:
    with build_client(
        tmp_path / "targets.db",
        tmp_path / "target-simulations",
    ) as client:
        simulation_id = create_started_simulation(client)

        target = client.post(
            f"/api/simulations/{simulation_id}/target",
            json={"x": 3.0, "y": -2.0},
        )
        waypoints = client.post(
            f"/api/simulations/{simulation_id}/waypoints",
            json={
                "waypoints": [
                    {"x": 2.0, "y": 1.0, "z": 5.0},
                    {"x": 4.0, "y": -1.0, "z": 5.0},
                ]
            },
        )
        outside = client.post(
            f"/api/simulations/{simulation_id}/target",
            json={"x": 30.0, "y": 0.0},
        )

    assert target.status_code == 200
    assert target.json()["target_position"] == {"x": 3.0, "y": -2.0, "z": 0.0}
    assert waypoints.status_code == 200
    assert len(waypoints.json()["waypoints"]) == 2
    assert outside.status_code == 409


def test_stop_saves_experiment_record_and_telemetry_json(tmp_path: Path) -> None:
    simulations_dir = tmp_path / "saved-simulations"
    with build_client(tmp_path / "experiments.db", simulations_dir) as client:
        simulation_id = create_started_simulation(client)
        client.post(
            f"/api/simulations/{simulation_id}/takeoff",
            json={"altitude_m": 4.0},
        )
        client.post(
            f"/api/simulations/{simulation_id}/target",
            json={"x": 2.0, "y": 3.0},
        )
        time.sleep(0.4)
        stopped = client.post(f"/api/simulations/{simulation_id}/stop")

        experiments = client.get("/api/experiments")
        replay = client.get(f"/api/experiments/{simulation_id}")

    assert stopped.status_code == 200
    assert experiments.status_code == 200
    records = experiments.json()
    assert len(records) == 1
    assert records[0]["aircraft_name"] == "EduQuad-650"
    assert records[0]["frame_count"] > 0
    assert records[0]["duration_s"] > 0

    assert replay.status_code == 200
    replay_document = replay.json()
    assert replay_document["experiment"]["id"] == simulation_id
    assert replay_document["aircraft"]["name"] == "EduQuad-650"
    assert replay_document["target_position"] == {"x": 2.0, "y": 3.0, "z": 4.0}
    assert len(replay_document["frames"]) == records[0]["frame_count"]
    assert {
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
    } == set(replay_document["frames"][0])
    assert (simulations_dir / f"{simulation_id}.json").exists()


def test_unknown_experiment_returns_not_found(tmp_path: Path) -> None:
    with build_client(
        tmp_path / "missing-experiment.db",
        tmp_path / "missing-simulations",
    ) as client:
        response = client.get("/api/experiments/999")

    assert response.status_code == 404
