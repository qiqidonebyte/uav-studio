from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.assembly_instances import default_assembly_instances
from backend.models import AircraftRecord
from backend.schemas import (
    AircraftDefinition,
    AircraftTemplate,
    AssemblyInstance,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_aircraft_metadata(session: Session) -> None:
    """Backfill portfolio metadata for legacy aircraft rows."""

    changed = False
    now = utc_now_iso()
    for record in session.scalars(select(AircraftRecord)).all():
        if record.description is None:
            record.description = ""
            changed = True
        if record.created_at is None:
            record.created_at = now
            changed = True
        if record.updated_at is None:
            record.updated_at = record.created_at or now
            changed = True
    if changed:
        session.commit()


def template_definitions() -> list[AircraftTemplate]:
    reference = AircraftDefinition(
        name="EduQuad-650 Reference",
        frame_id=1,
        motor_id=10,
        esc_id=20,
        propeller_id=30,
        battery_id=40,
        power_module_id=50,
        flight_controller_id=60,
        gnss_id=70,
        payload_id=80,
        gnss_position_m={"x": -0.16, "y": 0.0, "z": 0.08},
        payload_position_m={"x": 0.08, "y": 0.0, "z": -0.12},
    )
    reference = reference.model_copy(
        update={"assembly_instances": default_assembly_instances(reference)}
    )

    blank = AircraftDefinition(
        name="未命名 Quad-X",
        assembly_instances=[],
    )

    frame_450 = AircraftDefinition(
        name="EduQuad-450 Chassis",
        frame_id=2,
        assembly_instances=[
            AssemblyInstance(
                mount_id="frame:main",
                slot="frame",
                component_id=2,
            )
        ],
    )

    return [
        AircraftTemplate(
            key="reference-650",
            name="EduQuad-650 Reference",
            description="完整参考配置。适合从一架可直接验证和飞行的 650 四旋翼开始修改。",
            aircraft=reference,
        ),
        AircraftTemplate(
            key="blank-quad-x",
            name="空白 Quad-X",
            description="从零开始选择机架、动力、电源、飞控、导航和载荷。",
            aircraft=blank,
        ),
        AircraftTemplate(
            key="chassis-450",
            name="EduQuad-450 Chassis",
            description="仅预装 450 机架。当前 14/15 英寸桨与该机架会发生桨盘干涉，适合教学设计练习。",
            aircraft=frame_450,
        ),
    ]


def template_by_key(key: str) -> AircraftTemplate | None:
    return next((item for item in template_definitions() if item.key == key), None)


def duplicate_name(source_name: str) -> str:
    suffix = " - 副本"
    return source_name if source_name.endswith(suffix) else f"{source_name}{suffix}"
