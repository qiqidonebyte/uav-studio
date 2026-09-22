import math
from types import SimpleNamespace

import pytest

from backend.px4.bridge import Px4Bridge, Px4BridgeError, decode_sensor_health


def test_bridge_status_is_available_without_live_px4():
    bridge = Px4Bridge("udpin:0.0.0.0:14540")
    status = bridge.status()
    assert status["connected"] is False
    assert status["connection_url"] == "udpin:0.0.0.0:14540"
    assert "dependency_available" in status


def test_sensor_health_flags_decode_common_mavlink_bits():
    # gyro (bit 0), accelerometer (bit 1), magnetometer (bit 2), barometer (bit 3), GPS (bit 5)
    present = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 5)
    health = present & ~(1 << 2)
    decoded = decode_sensor_health({"present": present, "enabled": present, "health": health})
    assert decoded["gyro"]["healthy"] is True
    assert decoded["accelerometer"]["healthy"] is True
    assert decoded["magnetometer"]["healthy"] is False
    assert decoded["barometer"]["healthy"] is True
    assert decoded["gps"]["healthy"] is True


def test_telemetry_contract_contains_sensor_sections_without_connection():
    bridge = Px4Bridge("udpin:0.0.0.0:14540")
    telemetry = bridge.telemetry()
    assert "imu" in telemetry
    assert "magnetometer" in telemetry
    assert "barometer" in telemetry
    assert "sensor_health" in telemetry
    assert "sensor_data_age_s" in telemetry


class _Message:
    def __init__(self, msg_type: str, **values):
        self._msg_type = msg_type
        for key, value in values.items():
            setattr(self, key, value)

    def get_type(self):
        return self._msg_type


def test_scaled_imu_and_pressure_are_normalized_for_browser_contract():
    bridge = Px4Bridge("udpin:0.0.0.0:14540")
    bridge._handle_message(_Message(
        "SCALED_IMU",
        xacc=1000, yacc=0, zacc=-1000,
        xgyro=100, ygyro=-200, zgyro=0,
        xmag=300, ymag=400, zmag=0,
        temperature=2500,
    ))
    bridge._handle_message(_Message("SCALED_PRESSURE", press_abs=1008.4, temperature=2675))
    telemetry = bridge.telemetry()
    assert round(telemetry["imu"]["accel_m_s2"]["x"], 5) == 9.80665
    assert telemetry["imu"]["gyro_rad_s"]["x"] == 0.1
    assert telemetry["magnetometer"]["field_strength_gauss"] == 0.5
    assert telemetry["barometer"]["absolute_pressure_hpa"] == 1008.4
    assert telemetry["barometer"]["temperature_c"] == 26.75


def test_stop_all_motors_sends_disarmed_value_to_every_output(monkeypatch):
    bridge = Px4Bridge("udpin:0.0.0.0:14540")
    calls = []
    monkeypatch.setattr("backend.px4.bridge.mavutil", SimpleNamespace(
        mavlink=SimpleNamespace(MAV_CMD_ACTUATOR_TEST=310),
    ))
    monkeypatch.setattr(bridge, "telemetry", lambda: {"armed": False})
    monkeypatch.setattr(bridge, "_command", lambda command, params, timeout: calls.append((command, params, timeout)) or {"accepted": True})

    result = bridge.stop_all_motors()

    assert result["accepted"] is True
    assert len(calls) == 4
    assert [call[1][4] for call in calls] == [101.0, 102.0, 103.0, 104.0]
    assert all(math.isnan(call[1][0]) for call in calls)


def test_stop_all_motors_rejects_armed_vehicle(monkeypatch):
    bridge = Px4Bridge("udpin:0.0.0.0:14540")
    monkeypatch.setattr(bridge, "telemetry", lambda: {"armed": True})
    with pytest.raises(Px4BridgeError, match="已解锁"):
        bridge.stop_all_motors()
