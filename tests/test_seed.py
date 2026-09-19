from __future__ import annotations

import pytest

from backend.constants import MOTOR_ORDER, MOTOR_SPINS, motor_positions_m
from backend.engineering import calculate_aircraft_engineering, validate_configuration
from backend.schemas import parse_component_parameters
from backend.seed import build_seed_aircraft, build_seed_catalog


def test_seed_catalog_contains_all_v1_required_component_types() -> None:
    catalog = build_seed_catalog()
    component_types = {component.type for component in catalog.values()}

    required = {
        "frame",
        "motor",
        "esc",
        "propeller",
        "battery",
        "power_module",
        "flight_controller",
        "gnss",
        "payload",
    }
    assert required <= component_types


def test_seed_motor_curves_are_explicitly_educational_sample_data() -> None:
    catalog = build_seed_catalog()
    motor = catalog[10]
    parameters = parse_component_parameters(motor)

    assert {profile.propeller_id for profile in parameters.profiles} >= {30, 31}
    assert {profile.source for profile in parameters.profiles} == {"Educational Sample Data"}
    for profile in parameters.profiles:
        assert profile.points[0].throttle == 0.0
        assert profile.points[-1].throttle == 1.0


def test_quad_x_motor_order_positions_and_spins_are_frozen() -> None:
    positions = motor_positions_m(motor_diagonal_m=0.65)

    assert tuple(MOTOR_ORDER) == ("M1", "M2", "M3", "M4")
    assert MOTOR_SPINS == {"M1": "CCW", "M2": "CW", "M3": "CCW", "M4": "CW"}
    assert positions["M1"].x > 0.0 and positions["M1"].y > 0.0
    assert positions["M2"].x > 0.0 and positions["M2"].y < 0.0
    assert positions["M3"].x < 0.0 and positions["M3"].y < 0.0
    assert positions["M4"].x < 0.0 and positions["M4"].y > 0.0
    assert positions["M1"].z == pytest.approx(0.0)


def test_default_seed_aircraft_passes_engineering_validation() -> None:
    catalog = build_seed_catalog()
    aircraft = build_seed_aircraft()

    validation = validate_configuration(aircraft, catalog)
    summary = calculate_aircraft_engineering(aircraft, catalog)

    assert validation.passed is True
    assert not validation.blocking_errors
    assert summary.total_mass_kg > 1.0
    assert summary.max_total_thrust_n > summary.total_mass_kg * 9.80665
    assert summary.max_current_a > 0.0
    assert summary.hover_power_w > 0.0
    assert summary.estimated_flight_time_min > 0.0
