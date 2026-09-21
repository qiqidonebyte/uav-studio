from __future__ import annotations

import math
from typing import Any

from backend.px4.bridge import Px4Bridge, Px4BridgeError


class FlightValidationPx4Bridge(Px4Bridge):
    """PX4 bridge variant whose takeoff API accepts relative altitude.

    The existing browser API works with a relative altitude above home. PX4's
    MAV_CMD_NAV_TAKEOFF param7 is AMSL, so this class converts the target using
    GLOBAL_POSITION_INT before sending the command.
    """

    def __init__(self, connection_url: str | None = None) -> None:
        super().__init__(connection_url)
        self._alt_amsl_m: float | None = None

    def reconnect(self, connection_url: str | None = None) -> None:
        self._alt_amsl_m = None
        super().reconnect(connection_url)

    def _handle_message(self, message: Any) -> None:
        super()._handle_message(message)
        try:
            if message.get_type() != "GLOBAL_POSITION_INT":
                return
            raw_alt = getattr(message, "alt", None)
            if raw_alt is None:
                return
            value = float(raw_alt) / 1000.0
            if math.isfinite(value):
                self._alt_amsl_m = value
        except Exception:
            return

    def telemetry(self) -> dict[str, Any]:
        payload = super().telemetry()
        global_position = dict(payload.get("global_position") or {})
        global_position["alt_amsl_m"] = self._alt_amsl_m
        payload["global_position"] = global_position
        return payload

    def takeoff(self, altitude_m: float = 2.0) -> dict[str, Any]:
        if altitude_m <= 0 or altitude_m > 30:
            raise Px4BridgeError("PX4 起飞相对高度必须在 0-30 m")

        telemetry = self.telemetry()
        global_position = telemetry.get("global_position") or {}
        current_amsl = self._alt_amsl_m
        relative_alt = global_position.get("relative_alt_m")
        if current_amsl is None:
            raise Px4BridgeError(
                "尚未获得 GLOBAL_POSITION_INT 的 AMSL 高度，无法安全计算起飞目标高度"
            )

        relative_altitude = (
            float(relative_alt)
            if isinstance(relative_alt, (int, float))
            and math.isfinite(float(relative_alt))
            else 0.0
        )
        home_amsl = current_amsl - relative_altitude
        target_amsl = home_amsl + float(altitude_m)
        nan = float("nan")
        result = self._command(
            22,  # MAV_CMD_NAV_TAKEOFF
            [0.0, 0.0, 0.0, nan, nan, nan, target_amsl],
            timeout=5.0,
        )
        return {
            **result,
            "relative_altitude_m": float(altitude_m),
            "home_altitude_amsl_m": home_amsl,
            "target_altitude_amsl_m": target_amsl,
        }
