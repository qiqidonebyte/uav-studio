from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas import (
    AircraftDefinition,
    Component,
    MotorParameters,
    PropellerParameters,
    Vector3,
    parse_component_parameters,
)


def test_component_accepts_frozen_component_types() -> None:
    component = Component(
        id=10,
        name="EduMotor-5010",
        type="motor",
        mass_kg=0.18,
        parameters_json={"kv": 360, "profiles": []},
    )

    assert component.type == "motor"
    assert component.mass_kg == pytest.approx(0.18)


def test_component_rejects_unknown_type_and_non_positive_mass() -> None:
    with pytest.raises(ValidationError):
        Component(id=1, name="Unknown", type="camera", mass_kg=0.1, parameters_json={})

    with pytest.raises(ValidationError):
        Component(id=1, name="Invalid", type="frame", mass_kg=0.0, parameters_json={})


def test_motor_parameters_validate_curve_order_and_propeller_id() -> None:
    parameters = MotorParameters.model_validate(
        {
            "kv": 360,
            "profiles": [
                {
                    "battery_voltage_v": 22.2,
                    "propeller_id": 30,
                    "source": "Educational Sample Data",
                    "points": [
                        {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                        {"throttle": 0.5, "thrust_n": 9.8, "current_a": 8.5, "power_w": 189.0},
                        {"throttle": 1.0, "thrust_n": 22.0, "current_a": 22.0, "power_w": 488.0},
                    ],
                }
            ],
        }
    )

    assert parameters.profiles[0].propeller_id == 30
    assert parameters.profiles[0].points[-1].thrust_n == pytest.approx(22.0)

    with pytest.raises(ValidationError):
        MotorParameters.model_validate(
            {
                "kv": 360,
                "profiles": [
                    {
                        "battery_voltage_v": 22.2,
                        "propeller_id": 30,
                        "points": [
                            {"throttle": 0.5, "thrust_n": 9.8, "current_a": 8.5, "power_w": 189.0},
                            {"throttle": 0.5, "thrust_n": 10.0, "current_a": 9.0, "power_w": 200.0},
                        ],
                    }
                ],
            }
        )


def test_parse_component_parameters_is_type_specific() -> None:
    component = Component(
        id=30,
        name="EduProp-15x5",
        type="propeller",
        mass_kg=0.02,
        parameters_json={"diameter_in": 15.0, "pitch_in": 5.0, "direction": "PAIR"},
    )

    parameters = parse_component_parameters(component)

    assert isinstance(parameters, PropellerParameters)
    assert parameters.direction == "PAIR"


def test_aircraft_definition_supports_incomplete_draft_and_mount_positions() -> None:
    draft = AircraftDefinition(name="Draft", frame_id=1)

    assert draft.motor_id is None
    assert draft.payload_position_m is None

    complete = AircraftDefinition(
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
        gnss_position_m=Vector3(x=-0.15, y=0.0, z=0.08),
        payload_position_m=Vector3(x=0.1, y=0.0, z=-0.12),
    )

    assert complete.gnss_position_m is not None
    assert complete.model_dump(mode="json")["gnss_position_m"] == {
        "x": -0.15,
        "y": 0.0,
        "z": 0.08,
    }
