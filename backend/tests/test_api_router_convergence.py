from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "app" / "api" / "v1" / "api.py"


def test_api_router_registers_all_existing_major_endpoint_modules() -> None:
    source = API.read_text(encoding="utf-8")
    required = [
        "health_router",
        "auth_router",
        "patients_router",
        "visits_router",
        "opd_tokens_router",
        "prescriptions_router",
        "medicines_router",
        "stock_transactions_router",
        "stock_cards_router",
        "admissions_router",
        "discharge_router",
        "investigations_router",
        "investigation_results_router",
        "billing_router",
        "case_records_router",
        "patient_files_router",
        "archive_records_router",
        "medical_documents_router",
        "patient_history_router",
        "settings_router",
        "administration_router",
        "maintenance_router",
        "operational_year_router",
        "goods_receipts_router",
    ]
    for name in required:
        assert f"{name}" in source
        assert f"include_router({name})" in source or f"for router in" in source
