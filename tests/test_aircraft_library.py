from __future__ import annotations

from sqlalchemy import select

from backend.aircraft_library import (
    duplicate_name,
    ensure_aircraft_metadata,
    template_by_key,
    template_definitions,
)
from backend.database import build_engine, build_session_factory
from backend.models import AircraftRecord, Base


def test_aircraft_templates_are_stable_and_reference_650_is_fully_assembled() -> None:
    templates = template_definitions()
    assert {item.key for item in templates} == {
        "reference-650",
        "blank-quad-x",
        "chassis-450",
    }

    reference = template_by_key("reference-650")
    assert reference is not None
    assert reference.aircraft.id is None
    assert reference.aircraft.frame_id == 1
    assert reference.aircraft.motor_id == 10
    assert reference.aircraft.propeller_id == 30
    assert len(reference.aircraft.assembly_instances) == 18

    blank = template_by_key("blank-quad-x")
    assert blank is not None
    assert blank.aircraft.frame_id is None
    assert blank.aircraft.assembly_instances == []

    chassis = template_by_key("chassis-450")
    assert chassis is not None
    assert chassis.aircraft.frame_id == 2
    assert [item.mount_id for item in chassis.aircraft.assembly_instances] == ["frame:main"]


def test_template_objects_are_new_values_not_shared_mutable_state() -> None:
    first = template_by_key("reference-650")
    second = template_by_key("reference-650")
    assert first is not None and second is not None
    assert first is not second
    assert first.aircraft is not second.aircraft


def test_duplicate_name_is_predictable() -> None:
    assert duplicate_name("长航时巡检机") == "长航时巡检机 - 副本"
    assert duplicate_name("长航时巡检机 - 副本") == "长航时巡检机 - 副本"


def test_legacy_aircraft_metadata_is_backfilled() -> None:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)

    with factory() as session:
        session.add(AircraftRecord(name="Legacy Design"))
        session.commit()
        ensure_aircraft_metadata(session)

        record = session.scalar(select(AircraftRecord))
        assert record is not None
        assert record.description == ""
        assert record.created_at
        assert record.updated_at

    engine.dispose()
