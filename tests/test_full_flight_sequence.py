from __future__ import annotations

from backend.engineering import calculate_aircraft_engineering
from backend.seed import build_seed_aircraft, build_seed_catalog
from backend.simulator import SimpleSimulator


def test_default_eduquad_completes_full_flight_sequence() -> None:
    catalog = build_seed_catalog()
    aircraft = build_seed_aircraft()
    engineering = calculate_aircraft_engineering(aircraft, catalog)
    simulator = SimpleSimulator(aircraft, catalog, engineering)

    simulator.start()
    simulator.arm()
    simulator.takeoff(10.0)

    for _ in range(1500):
        simulator.step()
        if simulator.telemetry_frame().flight_mode == "HOVERING":
            break

    hover = simulator.telemetry_frame()
    assert hover.flight_mode == "HOVERING"
    assert hover.position.z > 9.6
    assert abs(hover.velocity.z) < 0.2

    battery_before_wind = hover.power.battery_remaining
    simulator.set_wind(speed_mps=5.0, direction_deg=90.0)
    maximum_horizontal_offset = 0.0
    maximum_tilt = 0.0
    maximum_output_difference = 0.0
    maximum_thrust_difference = 0.0
    maximum_horizontal_speed = 0.0

    for _ in range(1500):
        simulator.step()
        frame = simulator.telemetry_frame()
        maximum_horizontal_offset = max(
            maximum_horizontal_offset,
            (frame.position.x**2 + frame.position.y**2) ** 0.5,
        )
        maximum_tilt = max(
            maximum_tilt,
            abs(frame.attitude.roll),
            abs(frame.attitude.pitch),
        )
        maximum_output_difference = max(
            maximum_output_difference,
            max(frame.motors.outputs) - min(frame.motors.outputs),
        )
        maximum_thrust_difference = max(
            maximum_thrust_difference,
            max(frame.motors.thrusts_n) - min(frame.motors.thrusts_n),
        )
        maximum_horizontal_speed = max(
            maximum_horizontal_speed,
            abs(frame.velocity.y),
        )

    wind_frame = simulator.telemetry_frame()
    assert maximum_horizontal_offset > 0.5
    assert maximum_tilt > 0.01
    assert maximum_output_difference > 0.01
    assert maximum_thrust_difference > 0.1
    assert maximum_horizontal_speed > 0.05
    assert abs(wind_frame.velocity.y) < 0.2
    assert wind_frame.power.battery_remaining < battery_before_wind

    simulator.land()
    for _ in range(1500):
        simulator.step()
        if simulator.telemetry_frame().flight_mode == "IDLE":
            break

    landed = simulator.telemetry_frame()
    assert landed.position.z < 0.1
    assert landed.flight_mode == "IDLE"
    assert landed.armed is False
    assert max(landed.motors.outputs) < 0.02
    assert landed.power.battery_remaining < hover.power.battery_remaining
