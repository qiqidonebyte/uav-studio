from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PID:
    kp: float
    ki: float
    kd: float
    output_min: float
    output_max: float
    integral_min: float
    integral_max: float

    def __post_init__(self) -> None:
        if self.output_min >= self.output_max:
            raise ValueError("output_min must be lower than output_max")
        if self.integral_min >= self.integral_max:
            raise ValueError("integral_min must be lower than integral_max")
        self.reset()

    @property
    def integral(self) -> float:
        return self._integral

    def reset(self) -> None:
        self._integral = 0.0
        self._previous_error: float | None = None

    def step(self, error: float, dt: float) -> float:
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        self._integral = max(
            self.integral_min,
            min(self.integral_max, self._integral + error * dt),
        )
        derivative = (
            0.0
            if self._previous_error is None
            else (error - self._previous_error) / dt
        )
        self._previous_error = error

        output = (
            self.kp * error
            + self.ki * self._integral
            + self.kd * derivative
        )
        return max(self.output_min, min(self.output_max, output))
