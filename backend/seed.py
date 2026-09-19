from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import AircraftRecord, ComponentRecord
from backend.schemas import AircraftDefinition, Component, Vector3

EDUCATIONAL_SAMPLE_DATA = "Educational Sample Data"


def _voltage_profile(
    voltage_v: float,
    propeller_id: int,
    full_thrust_n: float,
    full_current_a: float,
    full_power_w: float,
) -> dict:
    return {
        "battery_voltage_v": voltage_v,
        "propeller_id": propeller_id,
        "source": EDUCATIONAL_SAMPLE_DATA,
        "points": [
            {
                "throttle": 0.25,
                "thrust_n": round(full_thrust_n * 0.16, 3),
                "current_a": round(full_current_a * 0.13, 3),
                "power_w": round(full_power_w * 0.13, 3),
            },
            {
                "throttle": 0.5,
                "thrust_n": round(full_thrust_n * 0.45, 3),
                "current_a": round(full_current_a * 0.39, 3),
                "power_w": round(full_power_w * 0.39, 3),
            },
            {
                "throttle": 0.75,
                "thrust_n": round(full_thrust_n * 0.73, 3),
                "current_a": round(full_current_a * 0.70, 3),
                "power_w": round(full_power_w * 0.70, 3),
            },
            {
                "throttle": 1.0,
                "thrust_n": full_thrust_n,
                "current_a": full_current_a,
                "power_w": full_power_w,
            },
        ],
    }


def _zero_point() -> dict:
    return {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0}


def _profile(
    voltage_v: float,
    propeller_id: int,
    full_thrust_n: float,
    full_current_a: float,
    full_power_w: float,
) -> dict:
    profile = _voltage_profile(
        voltage_v,
        propeller_id,
        full_thrust_n,
        full_current_a,
        full_power_w,
    )
    profile["points"].insert(0, _zero_point())
    return profile


def build_seed_catalog() -> dict[int, Component]:
    components = [
        Component(
            id=1,
            name="EduFrame-650",
            type="frame",
            mass_kg=0.45,
            parameters_json={
                "motor_diagonal_m": 0.65,
                "battery_position_m": {"x": -0.03, "y": 0.0, "z": -0.10},
                "power_module_position_m": {"x": 0.0, "y": 0.0, "z": 0.02},
                "flight_controller_position_m": {"x": 0.0, "y": 0.0, "z": 0.05},
                "gnss_mount_position_m": {"x": -0.16, "y": 0.0, "z": 0.08},
            },
        ),
        Component(
            id=2,
            name="EduFrame-450",
            type="frame",
            mass_kg=0.30,
            parameters_json={
                "motor_diagonal_m": 0.45,
                "battery_position_m": {"x": -0.02, "y": 0.0, "z": -0.08},
                "power_module_position_m": {"x": 0.0, "y": 0.0, "z": 0.015},
                "flight_controller_position_m": {"x": 0.0, "y": 0.0, "z": 0.035},
                "gnss_mount_position_m": {"x": -0.12, "y": 0.0, "z": 0.06},
            },
        ),
        Component(
            id=10,
            name="EduMotor-5010-360KV",
            type="motor",
            mass_kg=0.18,
            parameters_json={
                "kv": 360.0,
                "profiles": [
                    _profile(22.2, 30, 22.0, 22.0, 488.0),
                    _profile(25.2, 30, 26.0, 25.0, 630.0),
                    _profile(22.2, 31, 17.0, 18.0, 400.0),
                    _profile(25.2, 31, 20.0, 21.0, 529.0),
                ],
            },
        ),
        Component(
            id=11,
            name="EduMotor-4008-500KV",
            type="motor",
            mass_kg=0.12,
            parameters_json={
                "kv": 500.0,
                "profiles": [
                    _profile(22.2, 31, 14.0, 15.0, 333.0),
                    _profile(25.2, 31, 17.0, 18.0, 454.0),
                ],
            },
        ),
        Component(
            id=20,
            name="EduESC-30A",
            type="esc",
            mass_kg=0.035,
            parameters_json={
                "max_current_a": 40.0,
                "voltage_min_v": 12.0,
                "voltage_max_v": 30.0,
            },
        ),
        Component(
            id=21,
            name="EduESC-40A",
            type="esc",
            mass_kg=0.045,
            parameters_json={
                "max_current_a": 50.0,
                "voltage_min_v": 12.0,
                "voltage_max_v": 30.0,
            },
        ),
        Component(
            id=30,
            name="EduProp-15x5",
            type="propeller",
            mass_kg=0.025,
            parameters_json={
                "diameter_in": 15.0,
                "pitch_in": 5.0,
                "direction": "PAIR",
            },
        ),
        Component(
            id=31,
            name="EduProp-14x4.8",
            type="propeller",
            mass_kg=0.018,
            parameters_json={
                "diameter_in": 14.0,
                "pitch_in": 4.8,
                "direction": "PAIR",
            },
        ),
        Component(
            id=40,
            name="EduBattery-6S-10000",
            type="battery",
            mass_kg=1.05,
            parameters_json={
                "cell_count": 6,
                "capacity_mah": 10000.0,
                "nominal_voltage_v": 22.2,
                "voltage_min_v": 18.0,
                "voltage_max_v": 25.2,
                "max_continuous_current_a": 100.0,
                "usable_capacity_ratio": 0.8,
            },
        ),
        Component(
            id=41,
            name="EduBattery-6S-16000",
            type="battery",
            mass_kg=1.55,
            parameters_json={
                "cell_count": 6,
                "capacity_mah": 16000.0,
                "nominal_voltage_v": 22.2,
                "voltage_min_v": 18.0,
                "voltage_max_v": 25.2,
                "max_continuous_current_a": 160.0,
                "usable_capacity_ratio": 0.8,
            },
        ),
        Component(
            id=50,
            name="EduPower-120A",
            type="power_module",
            mass_kg=0.06,
            parameters_json={
                "max_current_a": 120.0,
                "voltage_min_v": 12.0,
                "voltage_max_v": 30.0,
            },
        ),
        Component(
            id=51,
            name="EduPower-160A",
            type="power_module",
            mass_kg=0.08,
            parameters_json={
                "max_current_a": 160.0,
                "voltage_min_v": 12.0,
                "voltage_max_v": 30.0,
            },
        ),
        Component(
            id=60,
            name="EduFC-V1",
            type="flight_controller",
            mass_kg=0.06,
            parameters_json={"voltage_min_v": 5.0, "voltage_max_v": 30.0},
        ),
        Component(
            id=61,
            name="EduFC-V2",
            type="flight_controller",
            mass_kg=0.055,
            parameters_json={"voltage_min_v": 5.0, "voltage_max_v": 30.0},
        ),
        Component(
            id=70,
            name="M8N",
            type="gnss",
            mass_kg=0.04,
            parameters_json={"voltage_min_v": 4.5, "voltage_max_v": 5.5},
        ),
        Component(
            id=80,
            name="EduCamera-300g",
            type="payload",
            mass_kg=0.30,
            parameters_json={"mount": "bottom_center"},
        ),
    ]
    return {component.id: component for component in components}


def build_seed_aircraft() -> AircraftDefinition:
    return AircraftDefinition(
        id=1,
        name="EduQuad-650",
        frame_id=1,
        motor_id=10,
        esc_id=20,
        propeller_id=30,
        battery_id=40,
        power_module_id=50,
        flight_controller_id=60,
        gnss_id=70,
        payload_id=80,
        gnss_position_m=Vector3(x=-0.16, y=0.0, z=0.08),
        payload_position_m=Vector3(x=0.08, y=0.0, z=-0.12),
    )


def seed_database(session: Session) -> None:
    has_components = session.scalar(select(ComponentRecord.id).limit(1)) is not None
    if not has_components:
        session.add_all(
            [
                ComponentRecord(
                    id=component.id,
                    name=component.name,
                    type=component.type,
                    mass_kg=component.mass_kg,
                    parameters_json=component.parameters_json,
                )
                for component in build_seed_catalog().values()
            ]
        )

    has_aircraft = session.scalar(select(AircraftRecord.id).limit(1)) is not None
    if not has_aircraft:
        aircraft = build_seed_aircraft()
        session.add(
            AircraftRecord(
                id=aircraft.id,
                name=aircraft.name,
                frame_id=aircraft.frame_id,
                motor_id=aircraft.motor_id,
                esc_id=aircraft.esc_id,
                propeller_id=aircraft.propeller_id,
                battery_id=aircraft.battery_id,
                power_module_id=aircraft.power_module_id,
                flight_controller_id=aircraft.flight_controller_id,
                gnss_id=aircraft.gnss_id,
                payload_id=aircraft.payload_id,
                gnss_position_json=(
                    aircraft.gnss_position_m.model_dump()
                    if aircraft.gnss_position_m is not None
                    else None
                ),
                payload_position_json=(
                    aircraft.payload_position_m.model_dump()
                    if aircraft.payload_position_m is not None
                    else None
                ),
            )
        )
    session.commit()
