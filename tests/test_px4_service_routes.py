from __future__ import annotations

from fastapi.testclient import TestClient

from backend.px4 import Px4BridgeError
from backend import px4_service


def service_client(monkeypatch) -> TestClient:
    # Do not start a real MAVLink connection while testing HTTP validation and
    # error translation. The bridge behaviour itself is covered separately.
    monkeypatch.setattr(px4_service.bridge, "start", lambda: None)
    monkeypatch.setattr(px4_service.bridge, "stop", lambda: None)
    return TestClient(px4_service.app)


def test_px4_service_exposes_status_and_telemetry_contract(monkeypatch) -> None:
    monkeypatch.setattr(px4_service.bridge, "status", lambda: {"connected": False})
    monkeypatch.setattr(
        px4_service.bridge,
        "telemetry",
        lambda: {"armed": False, "sensor_health": {"gyro": {"healthy": True}}},
    )
    with service_client(monkeypatch) as client:
        health = client.get("/api/px4/health")
        telemetry = client.get("/api/px4/telemetry")

    assert health.status_code == 200
    assert health.json() == {"service": "uav-studio-px4-bridge", "connected": False}
    assert telemetry.status_code == 200
    assert telemetry.json()["sensor_health"]["gyro"]["healthy"] is True


def test_px4_service_motor_route_validates_name_and_forwards_safe_command(monkeypatch) -> None:
    calls: list[tuple[int, float, float]] = []
    monkeypatch.setattr(
        px4_service.bridge,
        "test_motor",
        lambda motor, value, timeout: calls.append((motor, value, timeout))
        or {"accepted": True, "motor": motor},
    )
    with service_client(monkeypatch) as client:
        invalid = client.post("/api/px4/motors/M5/test", json={})
        tested = client.post(
            "/api/px4/motors/m2/test",
            json={"value": 0.25, "timeout_s": 1.2},
        )

    assert invalid.status_code == 422
    assert tested.status_code == 200
    assert tested.json() == {"accepted": True, "motor": 2}
    assert calls == [(2, 0.25, 1.2)]


def test_px4_service_translates_bridge_safety_error_to_conflict(monkeypatch) -> None:
    def rejected():
        raise Px4BridgeError("飞行器已解锁，禁止执行该操作")

    monkeypatch.setattr(px4_service.bridge, "stop_all_motors", rejected)
    with service_client(monkeypatch) as client:
        response = client.post("/api/px4/motors/stop")

    assert response.status_code == 409
    assert "已解锁" in response.json()["detail"]
