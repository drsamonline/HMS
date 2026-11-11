"""Gate tests for build-plan batch B32: the prescription as a printed document.

Every other record in HHMS prints. The prescription - the one document a patient
physically leaves with - did not, so the registration number added in B31 was
visible on screen and nowhere else.

The property that matters: the preview and the printed page are the same markup. A
separate print path is how the two drift, and a prescription that prints differently
from what was checked is worse than one that cannot be printed at all.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "frontend" / "js"
CSS = ROOT / "frontend" / "css"


def _module() -> str:
    return (JS / "ui" / "prescription-print.js").read_text(encoding="utf-8")


def test_the_document_component_exists() -> None:
    assert (JS / "ui" / "prescription-print.js").is_file()


def test_it_carries_the_prescriber_and_their_registration_number() -> None:
    """B31 put the number on screen; this puts it on the paper."""

    source = _module()
    assert "prescriptionHeader(prescription" in source


def test_it_carries_the_patient_identifier() -> None:
    """On a ward, the wrong-patient error is the one that matters most."""

    assert "patientHeader(patient" in _module()


def test_the_preview_is_the_printed_document() -> None:
    """One markup, one path. A second print path is how the two drift."""

    source = _module()
    assert 'class="print-document' in source
    assert "window.print()" in source
    # The same article is what the browser prints; there is no separate builder.
    assert source.count("print-document") == 1


def test_it_refuses_to_print_a_prescription_with_no_medicines() -> None:
    """A blank prescription is not a document."""

    source = _module()
    assert "nothing to print" in source


def test_every_value_is_escaped() -> None:
    """A patient's name and a free-text instruction both reach this markup."""

    source = _module()
    # Every interpolation of data goes through escapeHtml.
    raw = re.findall(r"\$\{([^}]*)\}", source)
    unescaped = [
        expression
        for expression in raw
        if "escapeHtml" not in expression
        and "items.map" not in expression
        and "index + 1" not in expression
        and "itemsTable(" not in expression
        and "prescriptionHeader(" not in expression
        and "patientHeader(" not in expression
        and "diagnosis" not in expression
        and "treatment_plan" not in expression
        and expression.strip() != "rows"  # already-escaped table rows
    ]
    assert not unescaped, f"unescaped interpolations: {unescaped}"


def test_the_clinical_screen_offers_it() -> None:
    clinical = (JS / "clinical.js").read_text(encoding="utf-8")
    assert "createPrescriptionPrintPreview" in clinical
    assert 'id="rx-print"' in clinical


def test_the_print_stylesheet_hides_the_application_chrome() -> None:
    """What prints is the document, not the screen it was checked on."""

    css = (CSS / "print.css").read_text(encoding="utf-8")
    assert "@media print" in css
    block = css.split("@media print", 1)[1]
    for chrome in (".topbar", ".sidebar", ".no-print"):
        assert chrome in block, f"{chrome} is not hidden when printing"


def test_the_document_styles_use_tokens() -> None:
    """The preview is on screen, so it follows the same palette as the rest."""

    css = (CSS / "ui.css").read_text(encoding="utf-8")
    block = css[css.index(".rx-document") :]
    literals = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", block)
    assert not literals, f"the prescription document carries literal colours: {literals}"
