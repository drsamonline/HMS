"""HHMS API v1 router registration."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.admissions import router as admissions_router
from app.api.v1.endpoints.archive_records import router as archive_records_router
from app.api.v1.endpoints.audit_logs import router as audit_logs_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.beds import router as beds_router
from app.api.v1.endpoints.billing import router as billing_router
from app.api.v1.endpoints.case_records import router as case_records_router
from app.api.v1.endpoints.department_services import router as department_services_router
from app.api.v1.endpoints.designations import router as designations_router
from app.api.v1.endpoints.diagnoses import router as diagnoses_router
from app.api.v1.endpoints.discharges import router as discharge_router
from app.api.v1.endpoints.diet_charts import router as diet_chart_router
from app.api.v1.endpoints.followups import router as followups_router
from app.api.v1.endpoints.goods_receipts import router as goods_receipts_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.icd11 import router as icd11_router
from app.api.v1.endpoints.inventory_items import router as inventory_items_router
from app.api.v1.endpoints.investigations import router as investigations_router
from app.api.v1.endpoints.investigation_results import router as investigation_results_router
from app.api.v1.endpoints.ipd_assessments import router as ipd_assessment_router
from app.api.v1.endpoints.maintenance import router as maintenance_router
from app.api.v1.endpoints.medical_documents import router as medical_documents_router
from app.api.v1.endpoints.medicine_batches import router as medicine_batches_router
from app.api.v1.endpoints.medicines import router as medicines_router
from app.api.v1.endpoints.nutritional_assessments import router as nutritional_assessment_router
from app.api.v1.endpoints.opd_tokens import router as opd_tokens_router
from app.api.v1.endpoints.operational_year import router as operational_year_router
from app.api.v1.endpoints.pain_assessments import router as pain_assessment_router
from app.api.v1.endpoints.patient_files import router as patient_files_router
from app.api.v1.endpoints.patient_history import router as patient_history_router
from app.api.v1.endpoints.patients import router as patients_router
from app.api.v1.endpoints.prescriptions import router as prescriptions_router
from app.api.v1.endpoints.progress_notes import router as progress_note_router
from app.api.v1.endpoints.reporting import router as reporting_router
from app.api.v1.endpoints.service_activities import router as service_activities_router
from app.api.v1.endpoints.settings import router as settings_router
from app.api.v1.endpoints.statistics import router as statistics_router
from app.api.v1.endpoints.stock_cards import router as stock_cards_router
from app.api.v1.endpoints.stock_transactions import router as stock_transactions_router
from app.api.v1.endpoints.visits import router as visits_router

api_router = APIRouter()

# Core/session
for router in (health_router, auth_router, patients_router, visits_router, opd_tokens_router):
    api_router.include_router(router)

# Clinical + pharmacy
for router in (
    prescriptions_router,
    medicines_router,
    medicine_batches_router,
    stock_transactions_router,
    stock_cards_router,
    inventory_items_router,
    goods_receipts_router,
):
    api_router.include_router(router)

# IPD
for router in (beds_router, admissions_router, discharge_router, ipd_assessment_router):
    api_router.include_router(router)

# Laboratory / clinical assessments
for router in (
    investigations_router,
    investigation_results_router,
    diagnoses_router,
    followups_router,
    icd11_router,
    pain_assessment_router,
    nutritional_assessment_router,
    diet_chart_router,
    progress_note_router,
):
    api_router.include_router(router)

# Billing
api_router.include_router(billing_router)

# Clinical records / MRD / history
for router in (
    case_records_router,
    patient_files_router,
    archive_records_router,
    medical_documents_router,
    patient_history_router,
):
    api_router.include_router(router)

# Administration / reporting / system operations
for router in (
    department_services_router,
    service_activities_router,
    statistics_router,
    reporting_router,
    settings_router,
    administration_router,
    audit_logs_router,
    maintenance_router,
    designations_router,
    operational_year_router,
):
    api_router.include_router(router)


__all__ = ["api_router"]
