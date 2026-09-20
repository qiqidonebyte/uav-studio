from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
import importlib
import sys

# Inject the minimum current-schema surface needed by p0_validation.py so this
# package can execute the real augmentation code in isolation.
schemas = ModuleType("backend.schemas")


@dataclass
class AircraftDefinition:
    frame_id: int | None = None
    motor_id: int | None = 10
    esc_id: int | None = 20
    propeller_id: int | None = None
    battery_id: int | None = 40
    power_module_id: int | None = 50
    flight_controller_id: int | None = 60
    gnss_id: int | None = 70
    payload_id: int | None = 80


@dataclass
class AssemblyIssue:
    code: str
    severity: str
    message: str
    affected_slots: list[str] = field(default_factory=list)
    affected_mounts: list[str] = field(default_factory=list)

    def model_copy(self, update=None):
        values = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "affected_slots": list(self.affected_slots),
            "affected_mounts": list(self.affected_mounts),
        }
        values.update(update or {})
        return AssemblyIssue(**values)


@dataclass
class AssemblyValidationResult:
    blocking_errors: list[AssemblyIssue] = field(default_factory=list)
    warnings: list[AssemblyIssue] = field(default_factory=list)

    @property
    def passed(self):
        return not self.blocking_errors

    def model_copy(self, update=None):
        values = {
            "blocking_errors": list(self.blocking_errors),
            "warnings": list(self.warnings),
        }
        values.update(update or {})
        return AssemblyValidationResult(**values)


schemas.AircraftDefinition = AircraftDefinition
schemas.AssemblyIssue = AssemblyIssue
schemas.AssemblyValidationResult = AssemblyValidationResult
schemas.MotorName = str
sys.modules["backend.schemas"] = schemas

module = importlib.import_module("backend.p0_validation")

safe = module.augment_validation(
    AircraftDefinition(frame_id=1, propeller_id=30),
    AssemblyValidationResult(),
)
assert safe.passed
assert not any(i.code == "PROPELLER_FRAME_OVERLAP" for i in safe.blocking_errors)

bad = module.augment_validation(
    AircraftDefinition(frame_id=2, propeller_id=31),
    AssemblyValidationResult(),
)
issues = [i for i in bad.blocking_errors if i.code == "PROPELLER_FRAME_OVERLAP"]
assert len(issues) == 1
issue = issues[0]
assert issue.affected_slots == ["frame", "propeller"]
assert issue.affected_mounts == ["M1", "M2", "M3", "M4"]
assert "旋翼盘重叠" in issue.message

twice = module.augment_validation(AircraftDefinition(frame_id=2, propeller_id=31), bad)
assert sum(i.code == "PROPELLER_FRAME_OVERLAP" for i in twice.blocking_errors) == 1

print("PASS runtime p0_validation overlap integration")
