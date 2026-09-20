from __future__ import annotations

import sys
from types import ModuleType

# Runtime integration test for the portfolio routes. The artifact overlay does
# not contain every unchanged backend module, so unchanged services are stubbed
# before importing backend.main. Aircraft models/database/schemas/routes remain
# the real implementation from this package.

engineering = ModuleType("backend.engineering")


class EngineeringInputError(ValueError):
    pass


def validate_configuration(aircraft, catalog):
    from backend.schemas import AssemblyValidationResult
    return AssemblyValidationResult()


def calculate_aircraft_engineering(aircraft, catalog):
    from backend.schemas import (
        AircraftEngineeringSummary,
        AssemblyValidationResult,
        InertiaEstimate,
        Vector3,
    )
    return AircraftEngineeringSummary(
        total_mass_kg=2.9,
        center_of_gravity_m=Vector3(),
        inertia_kg_m2=InertiaEstimate(ixx=0.1, iyy=0.1, izz=0.2),
        max_thrust_per_motor_n=22.0,
        max_total_thrust_n=88.0,
        thrust_weight_ratio=3.0,
        hover_throttle=0.4,
        hover_thrust_per_motor_n=7.1,
        hover_current_a=20.0,
        max_current_a=88.0,
        hover_power_w=450.0,
        max_power_w=1900.0,
        battery_continuous_margin_a=20.0,
        esc_current_margin_a=8.0,
        power_module_current_margin_a=32.0,
        payload_mass_fraction=0.1,
        estimated_flight_time_min=18.0,
        validation=AssemblyValidationResult(),
    )


engineering.EngineeringInputError = EngineeringInputError
engineering.validate_configuration = validate_configuration
engineering.calculate_aircraft_engineering = calculate_aircraft_engineering
sys.modules["backend.engineering"] = engineering

experiments = ModuleType("backend.experiments")
experiments.list_experiments = lambda session: []
experiments.load_replay = lambda session, simulation_id: (_ for _ in ()).throw(FileNotFoundError())
experiments.save_experiment = lambda *args, **kwargs: None
sys.modules["backend.experiments"] = experiments

component_library = ModuleType("backend.component_library")
component_library.register_component_library_routes = lambda app, get_db: None
sys.modules["backend.component_library"] = component_library

user_settings = ModuleType("backend.user_settings")
user_settings.ensure_admin_user = lambda session: None
user_settings.register_user_settings_routes = lambda app, get_db: None
sys.modules["backend.user_settings"] = user_settings

seed = ModuleType("backend.seed")


def seed_database(session):
    from backend.models import AircraftRecord
    if session.get(AircraftRecord, 1) is None:
        session.add(
            AircraftRecord(
                id=1,
                name="Seed Aircraft",
                frame_id=1,
                motor_id=10,
                esc_id=20,
                propeller_id=30,
                battery_id=40,
                power_module_id=50,
                flight_controller_id=60,
                gnss_id=70,
                payload_id=80,
            )
        )
        session.commit()


seed.seed_database = seed_database
sys.modules["backend.seed"] = seed

simulation_manager = ModuleType("backend.simulation_manager")


class SimulationNotFoundError(KeyError):
    pass


class SimulationManager:
    def set_next_id(self, value):
        self.next_id = value

    async def shutdown(self):
        return None

    def require(self, simulation_id):
        raise SimulationNotFoundError(simulation_id)


simulation_manager.SimulationManager = SimulationManager
simulation_manager.SimulationNotFoundError = SimulationNotFoundError
sys.modules["backend.simulation_manager"] = simulation_manager

from fastapi.testclient import TestClient
from backend.main import create_app

app = create_app(database_url="sqlite:///:memory:")

with TestClient(app) as client:
    library = client.get("/api/aircraft")
    assert library.status_code == 200, library.text
    items = library.json()
    assert len(items) == 1
    assert items[0]["aircraft"]["name"] == "Seed Aircraft"
    assert items[0]["description"] == ""
    assert items[0]["created_at"]
    assert items[0]["updated_at"]

    templates = client.get("/api/aircraft/templates")
    assert templates.status_code == 200, templates.text
    assert {item["key"] for item in templates.json()} == {
        "reference-650",
        "blank-quad-x",
        "chassis-450",
    }

    created = client.post(
        "/api/aircraft/from-template/blank-quad-x",
        json={"name": "巡检方案 A", "description": "测试设计"},
    )
    assert created.status_code == 201, created.text
    created_item = created.json()
    created_id = created_item["aircraft"]["id"]
    assert created_item["aircraft"]["name"] == "巡检方案 A"
    assert created_item["description"] == "测试设计"

    duplicate = client.post(
        f"/api/aircraft/{created_id}/duplicate",
        json={},
    )
    assert duplicate.status_code == 201, duplicate.text
    duplicate_item = duplicate.json()
    duplicate_id = duplicate_item["aircraft"]["id"]
    assert duplicate_item["aircraft"]["name"] == "巡检方案 A - 副本"
    assert duplicate_id != created_id

    renamed = client.patch(
        f"/api/aircraft/{duplicate_id}/metadata",
        json={"name": "巡检方案 B", "description": "独立副本"},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["aircraft"]["name"] == "巡检方案 B"
    assert renamed.json()["description"] == "独立副本"

    reloaded = client.get(f"/api/aircraft/{duplicate_id}")
    assert reloaded.status_code == 200
    assert reloaded.json()["aircraft"]["name"] == "巡检方案 B"

    deleted = client.delete(f"/api/aircraft/{duplicate_id}")
    assert deleted.status_code == 204, deleted.text

    final_library = client.get("/api/aircraft").json()
    assert all(item["aircraft"]["id"] != duplicate_id for item in final_library)
    assert any(item["aircraft"]["id"] == created_id for item in final_library)

    # Designs with experiment history are protected for traceability.
    from backend.models import SimulationRecord
    with app.state.session_factory() as session:
        session.add(
            SimulationRecord(
                id=9001,
                aircraft_id=created_id,
                aircraft_name="巡检方案 A",
                started_at="2026-09-20T00:00:00+00:00",
                ended_at="2026-09-20T00:01:00+00:00",
                duration_s=60.0,
                max_altitude_m=10.0,
                status="COMPLETED",
                frame_count=10,
                target_position_json={"x": 0, "y": 0, "z": 0},
                waypoints_json=[],
                telemetry_file="dummy.json",
            )
        )
        session.commit()

    protected = client.delete(f"/api/aircraft/{created_id}")
    assert protected.status_code == 409
    assert "实验记录" in protected.json()["detail"]

    with app.state.session_factory() as session:
        record = session.get(SimulationRecord, 9001)
        session.delete(record)
        session.commit()

    cleanup = client.delete(f"/api/aircraft/{created_id}")
    assert cleanup.status_code == 204

    # The portfolio never allows deleting the final remaining design.
    last_design = client.delete("/api/aircraft/1")
    assert last_design.status_code == 409
    assert "至少保留一架" in last_design.json()["detail"]

print("PASS runtime Aircraft Library API: list/templates/create/duplicate/rename/reload/delete/guards")
