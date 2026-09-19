from __future__ import annotations

from copy import deepcopy

import pytest

from backend.engineering import (
    calculate_aircraft_engineering,
    calculate_center_of_gravity,
    estimate_inertia,
    interpolate_motor_performance,
    validate_configuration,
)
from backend.schemas import AircraftDefinition, Component


def issue_codes(result) -> set[str]:
    return {issue.code for issue in result.blocking_errors}


def warning_codes(result) -> set[str]:
    return {issue.code for issue in result.warnings}


def test_mass_cg_and_inertia_come_from_component_mass_points(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    summary = calculate_aircraft_engineering(aircraft_definition, component_catalog)

    assert summary.total_mass_kg == pytest.approx(2.75)
    assert summary.center_of_gravity_m.x > 0.0
    assert summary.inertia_kg_m2.ixx > 0.0
    assert summary.inertia_kg_m2.iyy > 0.0
    assert summary.inertia_kg_m2.izz > 0.0


def test_payload_moving_forward_moves_cg_forward(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    rear_payload = aircraft_definition.model_copy(
        update={"payload_position_m": aircraft_definition.payload_position_m.model_copy(update={"x": -0.10})}
    )
    front_payload = aircraft_definition.model_copy(
        update={"payload_position_m": aircraft_definition.payload_position_m.model_copy(update={"x": 0.20})}
    )

    rear_cg = calculate_center_of_gravity(rear_payload, component_catalog)
    front_cg = calculate_center_of_gravity(front_payload, component_catalog)
    rear_inertia = estimate_inertia(rear_payload, component_catalog)
    front_inertia = estimate_inertia(front_payload, component_catalog)

    assert front_cg.x > rear_cg.x
    assert front_inertia.iyy > rear_inertia.iyy


def test_motor_performance_interpolates_both_voltage_and_throttle(
    component_catalog: dict[int, Component],
) -> None:
    motor = component_catalog[10]

    point = interpolate_motor_performance(
        motor=motor,
        propeller_id=30,
        battery_voltage_v=22.0,
        throttle=1.0,
    )

    assert point.thrust_n == pytest.approx(12.0)
    assert point.current_a == pytest.approx(12.0)
    assert point.power_w == pytest.approx(240.0)


def test_propeller_change_selects_a_different_performance_curve(
    component_catalog: dict[int, Component],
) -> None:
    motor = component_catalog[10]

    large_prop = interpolate_motor_performance(motor, 30, 22.0, 1.0)
    small_prop = interpolate_motor_performance(motor, 31, 22.0, 1.0)

    assert large_prop.thrust_n > small_prop.thrust_n
    assert large_prop.current_a > small_prop.current_a


def test_engineering_summary_uses_same_mass_for_thrust_and_gravity(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    summary = calculate_aircraft_engineering(aircraft_definition, component_catalog)

    assert summary.max_total_thrust_n == pytest.approx(48.0)
    assert summary.thrust_weight_ratio == pytest.approx(48.0 / (2.75 * 9.80665), rel=1e-4)
    assert 0.5 < summary.hover_throttle < 1.0
    assert summary.hover_current_a > 0.0
    assert summary.max_current_a == pytest.approx(48.0)
    assert summary.max_power_w == pytest.approx(960.0)
    assert summary.estimated_flight_time_min > 0.0
    assert summary.validation.passed is True
    assert summary.estimation_note == "Educational Estimation"


def test_missing_required_component_blocks_flight(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    incomplete = aircraft_definition.model_copy(update={"motor_id": None})

    result = validate_configuration(incomplete, component_catalog)

    assert result.passed is False
    assert "REQUIRED_COMPONENT_MISSING" in issue_codes(result)


def test_insufficient_total_thrust_blocks_flight(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[10].parameters_json["profiles"] = [
        {
            "battery_voltage_v": 22.0,
            "propeller_id": 30,
            "source": "Educational Sample Data",
            "points": [
                {"throttle": 0.0, "thrust_n": 0.0, "current_a": 0.0, "power_w": 0.0},
                {"throttle": 1.0, "thrust_n": 2.0, "current_a": 2.0, "power_w": 20.0},
            ],
        }
    ]

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "INSUFFICIENT_TOTAL_THRUST" in issue_codes(result)


def test_esc_current_limit_blocks_flight(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[20].parameters_json["max_current_a"] = 5.0

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "ESC_CURRENT_LIMIT_EXCEEDED" in issue_codes(result)


def test_battery_discharge_limit_blocks_flight(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[40].parameters_json["max_continuous_current_a"] = 10.0

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "BATTERY_DISCHARGE_LIMIT_EXCEEDED" in issue_codes(result)


def test_power_module_current_limit_blocks_flight(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[50].parameters_json["max_current_a"] = 5.0

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "POWER_MODULE_CURRENT_LIMIT_EXCEEDED" in issue_codes(result)


def test_voltage_incompatibility_blocks_flight(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[20].parameters_json["voltage_max_v"] = 20.0

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "VOLTAGE_INCOMPATIBLE" in issue_codes(result)


def test_propeller_direction_pair_is_required(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[30].parameters_json["direction"] = "CW"

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "PROPELLER_DIRECTION_MISMATCH" in issue_codes(result)


def test_missing_performance_curve_blocks_flight_instead_of_silent_estimate(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    for profile in catalog[10].parameters_json["profiles"]:
        profile["propeller_id"] = 999

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is False
    assert "MOTOR_PERFORMANCE_CURVE_MISSING" in issue_codes(result)


def test_low_thrust_weight_ratio_is_warning_not_blocking_error(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    for profile in catalog[10].parameters_json["profiles"]:
        for point in profile["points"]:
            point["thrust_n"] *= 0.75
            point["current_a"] *= 0.75
            point["power_w"] *= 0.75

    result = validate_configuration(aircraft_definition, catalog)
    summary = calculate_aircraft_engineering(aircraft_definition, catalog)

    assert result.passed is True
    assert "LOW_THRUST_WEIGHT_RATIO" in warning_codes(result)
    assert 1.0 < summary.thrust_weight_ratio < 1.5


def test_short_estimated_endurance_is_a_warning(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[40].parameters_json["capacity_mah"] = 1000.0

    result = validate_configuration(aircraft_definition, catalog)
    summary = calculate_aircraft_engineering(aircraft_definition, catalog)

    assert result.passed is True
    assert "SHORT_ESTIMATED_ENDURANCE" in warning_codes(result)
    assert summary.estimated_flight_time_min < 10.0


def test_high_payload_mass_fraction_is_a_warning(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    catalog = deepcopy(component_catalog)
    catalog[80] = catalog[80].model_copy(update={"mass_kg": 1.20})

    result = validate_configuration(aircraft_definition, catalog)

    assert result.passed is True
    assert "HIGH_PAYLOAD_MASS_FRACTION" in warning_codes(result)


def test_large_cg_offset_is_a_warning(
    component_catalog: dict[int, Component],
    aircraft_definition: AircraftDefinition,
) -> None:
    shifted = aircraft_definition.model_copy(
        update={"payload_position_m": aircraft_definition.payload_position_m.model_copy(update={"y": 0.30})}
    )

    result = validate_configuration(shifted, component_catalog)

    assert result.passed is True
    assert "CG_OFFSET_WARNING" in warning_codes(result)
