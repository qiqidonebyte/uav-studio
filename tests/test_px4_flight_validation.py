from backend.px4_service import FlightValidationPx4Bridge


class FakeMessage:
    def __init__(self, kind: str, **values):
        self._kind = kind
        self.__dict__.update(values)

    def get_type(self):
        return self._kind


def test_global_position_exposes_amsl_altitude():
    bridge = FlightValidationPx4Bridge()
    bridge._handle_message(
        FakeMessage(
            "GLOBAL_POSITION_INT",
            lat=280000000,
            lon=1200000000,
            alt=500_000,
            relative_alt=1_000,
        )
    )
    payload = bridge.telemetry()["global_position"]
    assert payload["alt_amsl_m"] == 500.0
    assert payload["relative_alt_m"] == 1.0


def test_relative_takeoff_is_converted_to_amsl(monkeypatch):
    bridge = FlightValidationPx4Bridge()
    bridge._handle_message(
        FakeMessage(
            "GLOBAL_POSITION_INT",
            lat=280000000,
            lon=1200000000,
            alt=500_000,
            relative_alt=1_000,
        )
    )

    captured = {}

    def fake_command(command, params, timeout=3.0):
        captured["command"] = command
        captured["params"] = params
        return {"accepted": True, "timeout": False, "command": command}

    monkeypatch.setattr(bridge, "_command", fake_command)
    result = bridge.takeoff(2.0)

    # Current altitude is 500m AMSL and relative altitude is 1m,
    # therefore home is 499m AMSL and a 2m takeoff target is 501m AMSL.
    assert captured["command"] == 22
    assert captured["params"][6] == 501.0
    assert result["target_altitude_amsl_m"] == 501.0
