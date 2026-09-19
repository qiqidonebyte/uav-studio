from __future__ import annotations

from copy import deepcopy

import pytest

from backend.schemas import AircraftDefinition, Component, Vector3


def make_component(
    component_id: int,
    component_type: str,
    name: str,
    mass_kg: float,
    parameters_json: dict,
) -> Component:
    return Component(
        id=component_id,
        type=component_type,
        name=name,
        mass_kg=mass_kg,
        parameters_json=deepcopy(parameters_json),
    )


@pytest.fixture
def component_catalog() -> dict[int, Component]:
    motor_profiles = {
        "kv": 360,
        "profiles": [
            {
                "battery_voltage_v": 20.0,
                "propeller_id": 30,
                "source": "Educational Sample Data",
                "points": [
                    {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                    {"throttle": 0.5, "thrust_n": 5.0, "current_a": 5.0, "power_w": 100.0},
                    {"throttle": 1.0, "thrust_n": 10.0, "current_a": 10.0, "power_w": 200.0},
                ],
            },
            {
                "battery_voltage_v": 24.0,
                "propeller_id": 30,
                "source": "Educational Sample Data",
                "points": [
                    {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                    {"throttle": 0.5, "thrust_n": 7.0, "current_a": 7.0, "power_w": 140.0},
                    {"throttle": 1.0, "thrust_n": 14.0, "current_a": 14.0, "power_w": 280.0},
                ],
            },
            {
                "battery_voltage_v": 22.0,
                "propeller_id": 31,
                "source": "Educational Sample Data",
                "points": [
                    {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                    {"throttle": 0.5, "thrust_n": 3.5, "current_a": 4.0, "power_w": 80.0},
                    {"throttle": 1.0, "thrust_n": 7.0, "current_a": 8.0, "power_w": 160.0},
                ],
            },
        ],
    }

    components = [
        make_component(
            1,
            "frame",
            "EduFrame-650",
            0.5,
            {
                "motor_diagonal_m": 0.65,
                "battery_position_m": {"x": -0.02, "y": 0.0, "z": -0.08},
                "power_module_position_m": {"x": 0.0, "y": 0.0, "z": 0.02},
                "flight_controller_position_m": {"x": 0.0, "y": 0.0, "z": 0.04},
                "gnss_mount_position_m": {"x": -0.15, "y": 0.0, "z": 0.08},
            },
        ),
        make_component(10, "motor", "EduMotor-5010", 0.2, motor_profiles),
        make_component(
            20,
            "esc",
            "EduESC-30A",
            0.03,
            {"max_current_a": 100.0, "voltage_min_v": 12.0, "voltage_max_v": 30.0},
        ),
        make_component(
            30,
            "propeller",
            "EduProp-15x5",
            0.02,
            {"diameter_in": 15.0, "pitch_in": 5.0, "direction": "PAIR"},
        ),
        make_component(
            31,
            "propeller",
            "EduProp-14x4.8",
            0.018,
            {"diameter_in": 14.0, "pitch_in": 4.8, "direction": "PAIR"},
        ),
        make_component(
            40,
            "battery",
            "EduBattery-6S-10000",
            0.8,
            {
                "cell_count": 6,
                "capacity_mah": 10000.0,
                "nominal_voltage_v": 22.0,
                "voltage_min_v": 18.0,
                "voltage_max_v": 25.2,
                "max_continuous_current_a": 200.0,
                "usable_capacity_ratio": 0.8,
            },
        ),
        make_component(
            50,
            "power_module",
            "EduPower-120A",
            0.05,
            {"max_current_a": 100.0, "voltage_min_v": 12.0, "voltage_max_v": 30.0},
        ),
        make_component(
            60,
            "flight_controller",
            "EduFC-V1",
            0.06,
            {"voltage_min_v": 5.0, "voltage_max_v": 30.0},
        ),
        make_component(
            70,
            "gnss",
            "M8N",
            0.04,
            {"voltage_min_v": 4.5, "voltage_max_v": 5.5},
        ),
        make_component(
            80,
            "payload",
            "EduCamera-300g",
            0.3,
            {"mount": "bottom_center"},
        ),
    ]
    return {component.id: component for component in components}


@pytest.fixture
def aircraft_definition() -> AircraftDefinition:
    return AircraftDefinition(
        id=1,
        name="EduQuad-650-Test",
        frame_id=1,
        motor_id=10,
        esc_id=20,
        propeller_id=30,
        battery_id=40,
        power_module_id=50,
        flight_controller_id=60,
        gnss_id=70,
        payload_id=80,
        gnss_position_m=Vector3(x=-0.15, y=0.0, z=0.08),
        payload_position_m=Vector3(x=0.10, y=0.0, z=-0.12),
    )
