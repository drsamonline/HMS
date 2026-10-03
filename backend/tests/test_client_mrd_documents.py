"""Regression coverage for MRD medical-document management."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_medical_document_contract_exists() -> None:
    assert (ROOT / "app" / "models" / "medical_document.py").exists()
    assert (ROOT / "app" / "schemas" / "medical_document.py").exists()
    assert (ROOT / "app" / "services" / "medical_document.py").exists()
    assert (ROOT / "app" / "api" / "v1" / "endpoints" / "medical_documents.py").exists()
