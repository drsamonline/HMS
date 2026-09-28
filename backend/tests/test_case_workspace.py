"""Client case workspace contract tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_case_workspace_contains_all_narrative_sections() -> None:
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "js" / "clinical.js").read_text(encoding="utf-8")
    assert "Homoeopathic Case Record" in js
    for field in (
        "chief_complaints",
        "history_present_illness",
        "past_history",
        "family_history",
        "mental_generals",
        "physical_generals",
        "particulars",
        "female_history",
        "male_history",
        "surgical_history",
        "miasmatic_assessment",
        "prescribing_rationale",
    ):
        assert field in js

def test_case_workspace_modalities_support_agg_amel_and_additional_text() -> None:
    js = (ROOT / "frontend" / "js" / "clinical.js").read_text(encoding="utf-8")
    assert 'value="agg"' in js
    assert 'value="amel"' in js
    assert "data-mod-note" in js
    assert "additional" in js
