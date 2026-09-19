from __future__ import annotations

import pytest

from backend.pid import PID


def test_pid_output_has_correct_direction_and_respects_bounds() -> None:
    pid = PID(
        kp=2.0,
        ki=1.0,
        kd=0.5,
        output_min=-1.0,
        output_max=1.0,
        integral_min=-0.5,
        integral_max=0.5,
    )

    positive = pid.step(error=1.0, dt=0.1)
    assert positive == pytest.approx(1.0)

    pid.reset()
    negative = pid.step(error=-1.0, dt=0.1)
    assert negative == pytest.approx(-1.0)


def test_pid_reset_clears_integral_and_derivative_state() -> None:
    pid = PID(
        kp=0.0,
        ki=1.0,
        kd=0.0,
        output_min=-10.0,
        output_max=10.0,
        integral_min=-10.0,
        integral_max=10.0,
    )

    pid.step(error=1.0, dt=0.2)
    assert pid.integral == pytest.approx(0.2)

    pid.reset()
    output = pid.step(error=0.0, dt=0.2)

    assert pid.integral == pytest.approx(0.0)
    assert output == pytest.approx(0.0)


def test_pid_clamps_integral_and_handles_non_positive_dt() -> None:
    pid = PID(
        kp=0.0,
        ki=1.0,
        kd=0.0,
        output_min=-10.0,
        output_max=10.0,
        integral_min=-0.25,
        integral_max=0.25,
    )

    pid.step(error=10.0, dt=1.0)
    assert pid.integral == pytest.approx(0.25)

    with pytest.raises(ValueError):
        pid.step(error=1.0, dt=0.0)
