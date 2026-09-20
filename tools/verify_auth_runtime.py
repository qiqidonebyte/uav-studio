from __future__ import annotations

import sys
from types import ModuleType

# The overlay contains only changed files. Stub unchanged heavy services before
# importing backend.main so this verifier exercises the real auth/database/
# aircraft route implementation without requiring the whole simulator tree.

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
experiments.list_experiments = lambda session, owner_user_id=None: []
experiments.load_replay = lambda session, simulation_id, owner_user_id=None: (_ for _ in ()).throw(FileNotFoundError())
experiments.save_experiment = lambda *args, **kwargs: None
sys.modules["backend.experiments"] = experiments

component_library = ModuleType("backend.component_library")
component_library.register_component_library_routes = lambda app, get_db: None
sys.modules["backend.component_library"] = component_library

p0_validation = ModuleType("backend.p0_validation")
p0_validation.augment_validation = lambda aircraft, validation: validation
sys.modules["backend.p0_validation"] = p0_validation

seed = ModuleType("backend.seed")


def seed_database(session):
    from backend.models import AircraftRecord
    if session.get(AircraftRecord, 1) is None:
        session.add(
            AircraftRecord(
                id=1,
                name="Legacy Admin Aircraft",
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
    # Protected APIs are no longer anonymous admin access.
    anonymous = client.get("/api/aircraft")
    assert anonymous.status_code == 401, anonymous.text

    bad_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert bad_login.status_code == 401

    admin_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "123456"},
    )
    assert admin_login.status_code == 200, admin_login.text
    cookie_header = admin_login.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header
    admin_library = client.get("/api/aircraft")
    assert admin_library.status_code == 200
    assert [x["aircraft"]["name"] for x in admin_library.json()] == [
        "Legacy Admin Aircraft"
    ]

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 204
    assert client.get("/api/aircraft").status_code == 401

    # Register Alice and verify per-user settings + exactly 10-aircraft quota.
    alice_register = client.post(
        "/api/auth/register",
        json={
            "username": "alice_01",
            "display_name": "Alice",
            "password": "123456",
        },
    )
    assert alice_register.status_code == 201, alice_register.text
    alice = alice_register.json()["user"]
    assert alice["aircraft_limit"] == 10
    assert client.get("/api/aircraft").json() == []

    settings_payload = client.get("/api/settings").json()
    settings_payload["general"]["decimal_places"] = 3
    assert client.put("/api/settings", json=settings_payload).status_code == 200

    alice_ids: list[int] = []
    for index in range(10):
        created = client.post(
            "/api/aircraft/from-template/blank-quad-x",
            json={"name": f"Alice-{index + 1}", "description": "quota test"},
        )
        assert created.status_code == 201, (index, created.text)
        alice_ids.append(created.json()["aircraft"]["id"])

    library = client.get("/api/aircraft")
    assert library.status_code == 200
    assert len(library.json()) == 10

    eleventh = client.post(
        "/api/aircraft/from-template/blank-quad-x",
        json={"name": "Alice-11", "description": "must fail"},
    )
    assert eleventh.status_code == 409, eleventh.text
    assert "最多保存 10 架" in eleventh.json()["detail"]

    duplicate_at_limit = client.post(
        f"/api/aircraft/{alice_ids[0]}/duplicate",
        json={},
    )
    assert duplicate_at_limit.status_code == 409

    duplicate_username = client.post(
        "/api/auth/register",
        json={"username": "ALICE_01", "display_name": "Duplicate", "password": "123456"},
    )
    assert duplicate_username.status_code == 409

    assert client.post("/api/auth/logout").status_code == 204

    # Bob receives a clean isolated workspace and cannot address Alice's IDs.
    bob_register = client.post(
        "/api/auth/register",
        json={"username": "bob_01", "display_name": "Bob", "password": "123456"},
    )
    assert bob_register.status_code == 201
    assert client.get("/api/aircraft").json() == []
    bob_settings = client.get("/api/settings").json()
    assert bob_settings["general"]["decimal_places"] == 2

    forbidden_by_ownership = client.get(f"/api/aircraft/{alice_ids[0]}")
    assert forbidden_by_ownership.status_code == 404
    assert client.patch(
        f"/api/aircraft/{alice_ids[0]}/metadata",
        json={"name": "Bob must not rename Alice"},
    ).status_code == 404
    assert client.post(
        f"/api/aircraft/{alice_ids[0]}/duplicate",
        json={},
    ).status_code == 404
    assert client.delete(
        f"/api/aircraft/{alice_ids[0]}"
    ).status_code == 404
    assert client.post(
        "/api/simulations",
        json={"aircraft_id": alice_ids[0]},
    ).status_code == 404

    bob_aircraft = client.post(
        "/api/aircraft/from-template/reference-650",
        json={"name": "Bob Reference", "description": "private"},
    )
    assert bob_aircraft.status_code == 201
    assert len(client.get("/api/aircraft").json()) == 1

    assert client.post("/api/auth/logout").status_code == 204

    # Alice's persisted workspace/settings reappear after a new login session.
    alice_login = client.post(
        "/api/auth/login",
        json={"username": "alice_01", "password": "123456"},
    )
    assert alice_login.status_code == 200
    assert len(client.get("/api/aircraft").json()) == 10
    alice_settings = client.get("/api/settings").json()
    assert alice_settings["general"]["decimal_places"] == 3

print("PASS runtime auth/workspace: login/register/cookie/isolation/settings/10-aircraft-limit")
