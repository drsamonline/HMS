from pathlib import Path


def test_all_operational_endpoint_modules_are_registered():
    source = Path(__file__).parents[1] / 'app/api/v1/api.py'
    text = source.read_text(encoding='utf-8')
    required = [
        'administration_router', 'backups_router', 'departments_router',
        'dispenses_router', 'procurement_router', 'stock_batches_router',
        'patient_history_router', 'operational_year_router',
    ]
    for name in required:
        assert name in text


def test_router_module_has_no_undefined_administration_reference():
    text = (Path(__file__).parents[1] / 'app/api/v1/api.py').read_text(encoding='utf-8')
    assert 'administration_router' in text
    assert 'from app.api.v1.endpoints.administration import router as administration_router' in text
