from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class PropellerFitResult:
    frame_id: int
    propeller_id: int
    motor_diagonal_m: float
    adjacent_motor_spacing_m: float
    propeller_diameter_m: float
    clearance_m: float

    @property
    def overlaps(self) -> bool:
        return self.clearance_m < -1e-9


def rotor_disc_clearance_m(
    motor_diagonal_m: float,
    propeller_diameter_m: float,
) -> float:
    """Return adjacent rotor-disc tip clearance for a Quad-X layout.

    `motor_diagonal_m` is the M1↔M3 / M2↔M4 motor diagonal. Adjacent motor
    spacing is diagonal / sqrt(2). Positive means a physical gap; negative
    means the swept discs intersect.
    """
    if motor_diagonal_m <= 0:
        raise ValueError("motor_diagonal_m must be positive")
    if propeller_diameter_m <= 0:
        raise ValueError("propeller_diameter_m must be positive")
    return motor_diagonal_m / sqrt(2.0) - propeller_diameter_m


def fit_from_asset_manifest(
    manifest: dict[str, Any],
    frame_id: int | None,
    propeller_id: int | None,
) -> PropellerFitResult | None:
    """Resolve visual rotor fit for manifest-known component assets.

    Unknown/custom component IDs deliberately return None instead of guessing.
    The runtime engineering validator remains the authority for arbitrary
    custom components; this guard prevents known checked-in GLB combinations
    from displaying physically impossible rotor overlap.
    """
    if frame_id is None or propeller_id is None:
        return None
    component_map = manifest.get("componentMap")
    if not isinstance(component_map, dict):
        return None
    frame = component_map.get(str(frame_id))
    propeller = component_map.get(str(propeller_id))
    if not isinstance(frame, dict) or not isinstance(propeller, dict):
        return None

    diagonal = frame.get("motor_diagonal_m")
    diameter = propeller.get("swept_diameter_m")
    if not isinstance(diagonal, (int, float)) or not isinstance(diameter, (int, float)):
        return None

    diagonal_m = float(diagonal)
    diameter_m = float(diameter)
    clearance = rotor_disc_clearance_m(diagonal_m, diameter_m)
    return PropellerFitResult(
        frame_id=frame_id,
        propeller_id=propeller_id,
        motor_diagonal_m=diagonal_m,
        adjacent_motor_spacing_m=diagonal_m / sqrt(2.0),
        propeller_diameter_m=diameter_m,
        clearance_m=clearance,
    )
