from __future__ import annotations

from math import isfinite

import pytest

from backend.engineering import calculate_aircraft_engineering
from backend.schemas import AircraftDefinition, Component
from backend.simulator import SimpleSimulator


def build_simulator(
    aircraft: AircraftDefinition,
    catalog: dict[int, Component],
) -> SimpleSimulator:
    engineering = calculate_aircraft_engineering(aircraft, catalog)
    return SimpleSimulator(aircraft=aircraft, catalog=catalog, engineering=engineering)


def takeoff_and_hover(
    simulator: SimpleSimulator,
    altitude_m: float,
    max_steps: int = 1200,
) -> None:
    simulator.start()
    simulator.arm()
    simulator.takeoff(altitude_m)
    for _ in range(max_steps):
        simulator.step()
        if simulator.telemetry_frame().flight_mode == "HOVERING":
            return
    raise AssertionError("simulator did not enter HOVERING")


def test_simulator_initial_state_is_disarmed_on_ground(
    aircraft_definition: AircraftDefinition,
    component_catalog: dict[int, Component],
) -> None:
    simulator = build_simulator(aircraft_definition, component_catalog)

    frame = simulator.telemetry_frame()

    assert frame.t == 0.0
    assert frame.flight_mode == "IDLE"
    assert frame.armed is False
    assert frame.position.z == 0.0
    assert frame.motors.outputs == pytest.approx([0.0, 0.0, 0.0, 0.0])
    assert frame.motors.thrusts_n == pytest.approx([0.0, 0.0, 0.0, 0.0])
    assert frame.forces.gravity_n == pytest.approx(2.75 * 9.80665)


def test_arm_takeoff_and_hover_follow_command_state(
    aircraft_definition: AircraftDefinition,
    component_catalog: dict[int, Component],
) -> None:
    simulator = build_simulator(aircraft_definition, component_catalog)

    simulator.start()
    simulator.arm()
    armed_frame = simulator.telemetry_frame()
    assert armed_frame.armed is True
    assert armed_frame.flight_mode == "ARMED"

    simulator.takeoff(5.0)
    assert simulator.telemetry_frame().flight_mode == "TAKING_OFF"
    takeoff_and_hover(simulator, 5.0, max_steps=800)
    frame = simulator.telemetry_frame()

    assert frame.position.z == pytest.approx(5.0, abs=0.3)
    assert abs(frame.velocity.z) < 0.2
    assert frame.flight_mode == "HOVERING"
    assert all(0.0 <= output <= 1.0 for output in frame.motors.outputs)
    assert all(thrust >= 0.0 for thrust in frame.motors.thrusts_n)


def test_wind_causes_position_attitude_and_motor_differences_then_recovery(
    aircraft_definition: AircraftDefinition,
    component_catalog: dict[int, Component],
) -> None:
    simulator = build_simulator(aircraft_definition, component_catalog)
    takeoff_and_hover(simulator, 5.0)

    simulator.set_wind(speed_mps=5.0, direction_deg=90.0)
    maximum_vy = 0.0
    maximum_output_difference = 0.0
    maximum_thrust_difference = 0.0
    for _ in range(500):
        simulator.step()
        frame = simulator.telemetry_frame()
        maximum_vy = max(maximum_vy, frame.velocity.y)
        maximum_output_difference = max(
            maximum_output_difference,
            max(frame.motors.outputs) - min(frame.motors.outputs),
        )
        maximum_thrust_difference = max(
            maximum_thrust_difference,
            max(frame.motors.thrusts_n) - min(frame.motors.thrusts_n),
        )

    frame = simulator.telemetry_frame()
    assert frame.wind.speed_mps == pytest.approx(5.0)
    assert frame.wind.direction_deg == pytest.approx(90.0)
    assert abs(frame.position.y) > 0.1
    assert abs(frame.attitude.roll) > 1e-4 or abs(frame.attitude.pitch) > 1e-4
    assert maximum_output_difference > 0.01
    assert maximum_thrust_difference > 0.1
    assert maximum_vy > 0.05
    assert abs(frame.velocity.y) < 0.2


def test_landing_returns_to_ground_and_disarms(
    aircraft_definition: AircraftDefinition,
    component_catalog: dict[int, Component],
) -> None:
    simulator = build_simulator(aircraft_definition, component_catalog)
    takeoff_and_hover(simulator, 3.0)

    simulator.land()
    for _ in range(1000):
        simulator.step()
        if simulator.telemetry_frame().flight_mode == "IDLE":
            break

    frame = simulator.telemetry_frame()
    assert frame.position.z < 0.1
    assert frame.flight_mode == "IDLE"
    assert frame.armed is False
    assert max(frame.motors.outputs) < 0.02


def test_pause_reset_and_ground_constraint(
    aircraft_definition: AircraftDefinition,
    component_catalog: dict[int, Component],
) -> None:
    simulator = build_simulator(aircraft_definition, component_catalog)
    simulator.start()
    simulator.arm()
    simulator.takeoff(5.0)
    for _ in range(50):
        simulator.step()

    simulator.pause()
    paused_frame = simulator.telemetry_frame()
    simulator.step()
    assert simulator.telemetry_frame() == paused_frame

    simulator.reset()
    reset_frame = simulator.telemetry_frame()
    assert reset_frame.t == 0.0
    assert reset_frame.position.z == 0.0
    assert reset_frame.flight_mode == "IDLE"
    assert reset_frame.armed is False

    simulator.start()
    simulator.arm()
    simulator.set_wind(20.0, 180.0)
    for _ in range(400):
        simulator.step()
    assert simulator.telemetry_frame().position.z >= 0.0


def test_simulator_outputs_remain_finite_and_battery_stays_bounded(
    aircraft_definition: AircraftDefinition,
    component_catalog: dict[int, Component],
) -> None:
    simulator = build_simulator(aircraft_definition, component_catalog)
    initial_battery = simulator.telemetry_frame().power.battery_remaining
    takeoff_and_hover(simulator, 8.0, max_steps=1200)

    for _ in range(3000):
        simulator.step()
        frame = simulator.telemetry_frame()
        values = [
            frame.t,
            frame.position.x,
            frame.position.y,
            frame.position.z,
            frame.velocity.x,
            frame.velocity.y,
            frame.velocity.z,
            frame.attitude.roll,
            frame.attitude.pitch,
            frame.attitude.yaw,
            *frame.motors.outputs,
            *frame.motors.thrusts_n,
            frame.power.battery_remaining,
            frame.power.voltage_v,
            frame.power.current_a,
        ]
        assert all(isfinite(value) for value in values)
        assert 0.0 <= frame.power.battery_remaining <= 1.0

    assert simulator.telemetry_frame().power.battery_remaining < initial_battery
