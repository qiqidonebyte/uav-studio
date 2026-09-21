from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StudentBrief(StrictModel):
    symptom: str = Field(min_length=1, max_length=500)
    task: str = Field(min_length=1, max_length=500)


class SuccessCondition(StrictModel):
    key: str = Field(min_length=1, max_length=80)
    group: Literal["repair", "validation"]


class FaultTrainingCase(StrictModel):
    id: str = Field(pattern=r"^F\d{2}_[A-Z0-9_]+$")
    title: str = Field(min_length=1, max_length=120)
    category: Literal["sensors", "rc", "power", "safety", "integrated"]
    difficulty: Literal[1, 2, 3]
    recommended_minutes: int = Field(ge=3, le=120)
    icon: str = Field(min_length=1, max_length=8)
    fault_source: str = Field(min_length=1, max_length=120)
    legacy_scenario: Literal["standard", "mapping", "compass", "failsafe"]
    initial_section: Literal["sensors", "rc", "power", "safety", "preflight"]
    target_sections: list[Literal["sensors", "rc", "power", "safety", "preflight"]] = Field(min_length=1)
    student_brief: StudentBrief
    injections: list[str] = Field(min_length=1)
    success_conditions: list[SuccessCondition] = Field(min_length=1)
    hints: list[str] = Field(min_length=1, max_length=4)


DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "frontend" / "public" / "training" / "scenarios" / "index.json"


def load_training_cases(path: Path | None = None) -> list[FaultTrainingCase]:
    catalog_path = path or DEFAULT_CATALOG
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("training scenario catalog must be a JSON array")
    cases = [FaultTrainingCase.model_validate(item) for item in raw]
    ids = [item.id for item in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("training scenario ids must be unique")
    return cases
