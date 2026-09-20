from backend.px4.bridge import Px4Bridge


class FakeMessage:
    def __init__(self, kind: str, **values):
        self._kind = kind
        self.__dict__.update(values)

    def get_type(self):
        return self._kind


def test_rc_channels_and_zero_rssi_are_preserved():
    bridge = Px4Bridge()
    values = {"chancount": 8, "rssi": 0}
    for index in range(1, 19):
        values[f"chan{index}_raw"] = 1500 if index <= 8 else 65535
    bridge._handle_message(FakeMessage("RC_CHANNELS", **values))

    rc = bridge.telemetry()["rc"]
    assert rc["channel_count"] == 8
    assert rc["channels_us"][:4] == [1500, 1500, 1500, 1500]
    assert rc["channels_us"][8] is None
    assert rc["rssi_percent"] == 0.0


def test_manual_control_is_observed_only():
    bridge = Px4Bridge()
    bridge._handle_message(
        FakeMessage("MANUAL_CONTROL", x=100, y=-200, z=500, r=50, buttons=3)
    )
    assert bridge.telemetry()["rc"]["manual_control"] == {
        "x": 100,
        "y": -200,
        "z": 500,
        "r": 50,
        "buttons": 3,
    }
