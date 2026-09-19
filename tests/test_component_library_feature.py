from __future__ import annotations

from pathlib import Path

from backend.component_library import (
    ComponentUpdateRequest,
    clone_library_component,
    get_library_component,
    list_library_components,
    update_library_component,
)
from backend.database import build_engine, build_session_factory
from backend.models import Base
from backend.seed import seed_database


def seeded_session():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = build_session_factory(engine)()
    seed_database(session)
    return engine, session


def test_library_lists_categories_search_and_visuals() -> None:
    engine, session = seeded_session()
    try:
        motors = list_library_components(session, component_type="motor")
        assert len(motors) >= 2
        assert all(item.type == "motor" for item in motors)
        assert all(item.visual is not None for item in motors)
        assert all(item.visual.thumbnail for item in motors if item.visual)

        search = list_library_components(session, search="5010")
        assert [item.id for item in search] == [10]
    finally:
        session.close()
        engine.dispose()



def test_library_visual_references_exist_on_disk() -> None:
    engine, session = seeded_session()
    try:
        base = Path(__file__).resolve().parents[1] / "frontend" / "public" / "models" / "uav" / "v1_1"
        for item in list_library_components(session):
            assert item.visual is not None
            for relative in (item.visual.file, item.visual.cw_file, item.visual.ccw_file, item.visual.thumbnail):
                if relative:
                    assert (base / relative).exists(), f"missing visual resource: {relative}"
    finally:
        session.close()
        engine.dispose()


def test_motor_compatibility_is_derived_from_performance_profiles() -> None:
    engine, session = seeded_session()
    try:
        motor = get_library_component(session, 10)
        by_label = {group.label: group for group in motor.compatibility}
        assert 30 in by_label["螺旋桨"].component_ids
        assert 31 in by_label["螺旋桨"].component_ids
        assert 40 in by_label["电池"].component_ids
    finally:
        session.close()
        engine.dispose()


def test_clone_component_reuses_visual_but_gets_new_identity() -> None:
    engine, session = seeded_session()
    try:
        source = get_library_component(session, 10)
        clone = clone_library_component(session, 10, name="课程自定义 5010")

        assert clone.id != source.id
        assert clone.name == "课程自定义 5010"
        assert clone.type == source.type
        assert clone.visual is not None and source.visual is not None
        assert clone.visual.file == source.visual.file
        assert clone.visual.asset_key != source.visual.asset_key
        assert "自定义" in clone.library.tags
    finally:
        session.close()
        engine.dispose()


def test_edit_component_preserves_visual_and_validates_engineering_contract() -> None:
    engine, session = seeded_session()
    try:
        before = get_library_component(session, 20)
        command = ComponentUpdateRequest(
            name="EduESC-30A-课程版",
            mass_kg=0.036,
            parameters_json={
                "max_current_a": 42.0,
                "voltage_min_v": 12.0,
                "voltage_max_v": 30.0,
            },
            notes="用于课堂比较",
            tags=["课程", "ESC"],
        )
        after = update_library_component(session, 20, command)
        assert after.name == "EduESC-30A-课程版"
        assert after.mass_kg == 0.036
        assert after.parameters_json["max_current_a"] == 42.0
        assert after.library.notes == "用于课堂比较"
        assert after.library.tags == ["课程", "ESC"]
        assert after.visual == before.visual

        invalid = command.model_copy(update={
            "parameters_json": {
                "max_current_a": 42.0,
                "voltage_min_v": 31.0,
                "voltage_max_v": 30.0,
            }
        })
        try:
            update_library_component(session, 20, invalid)
        except Exception:
            pass
        else:
            raise AssertionError("invalid ESC voltage contract should fail")
    finally:
        session.close()
        engine.dispose()
