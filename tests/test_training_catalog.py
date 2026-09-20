from backend.training import load_training_cases


def test_fault_training_catalog_contains_six_unique_cases():
    cases = load_training_cases()
    assert len(cases) == 6
    assert len({item.id for item in cases}) == 6
    assert {item.category for item in cases} >= {"sensors", "rc", "power", "safety", "integrated"}


def test_integrated_case_spans_multiple_debug_sections():
    cases = {item.id: item for item in load_training_cases()}
    integrated = cases["F06_INTEGRATED"]
    assert integrated.difficulty == 3
    assert {"rc", "power", "safety", "preflight"}.issubset(set(integrated.target_sections))
    assert len(integrated.success_conditions) >= 6
