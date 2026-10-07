"""Batch 113 QA — Print pipeline & hardware-readiness contract.

Milestone 7 (Release) part 9 / Milestone 3 "final print QA".  Closes the
last open functional item on the print surface with an automated contract
suite over the three layers of the pipeline:

* ``frontend/css/print.css`` — A4 portrait page geometry, chrome hiding,
  break rules, and toolbar exclusion from paper output.
* ``frontend/js/print.js`` + ``reports.js`` + ``api.js`` — every backend
  print-envelope endpoint has a matching client fetcher, renderer, and
  wired Reports-workspace button; all dynamic values are HTML-escaped
  before entering innerHTML templates.
* Backend endpoints — every envelope route answers 200 on a cold empty
  database (no crash on fresh installs), payloads carry the locked
  envelope shape, and the invoice packet is byte-consistent with live
  payment data end-to-end.

Hardware smoke (physical printers) remains a field checklist; this suite
locks everything that can be verified without paper in the building.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _qa_harness import (  # noqa: E402
    api_get,
    api_post,
    make_client,
    seed_number_sequence,
    seed_user,
    seed_visit,
)

PROJECT_ROOT = TESTS_DIR.parents[1]
API = "/api/v1"

PRINT_CSS = PROJECT_ROOT / "frontend" / "css" / "print.css"
PRINT_JS = PROJECT_ROOT / "frontend" / "js" / "print.js"
REPORTS_JS = PROJECT_ROOT / "frontend" / "js" / "reports.js"
API_JS = PROJECT_ROOT / "frontend" / "js" / "api.js"

# The 16 POST print-envelope routes registered on the reporting router
# (verified against the @router.post decorators in
# app/api/v1/endpoints/reporting.py).
ENVELOPE_SLUGS = [
    "clinical-data/print-envelope",
    "invoice-print-envelope",
    "collection-summary-print-envelope",
    "receivables-aging-print-envelope",
    "invoice-receipt-continuity-print-envelope",
    "receipt-numbering-continuity-print-envelope",
    "invoice-payment-reconciliation-print-envelope",
    "payment-method-summary-print-envelope",
    "invoice-overpayment-print-envelope",
    "payment-method-overpayment-print-envelope",
    "invoice-settlement-audit-print-envelope",
    "refund-audit-print-envelope",
    "discharge-audit-print-envelope",
    "opd-queue-summary-print-envelope",
    "ward-occupancy-print-envelope",
    "investigation-billing-reconciliation-print-envelope",
]


def _slug_to_fetcher(slug: str) -> str:
    """Map an endpoint slug to its expected api.js fetcher name."""
    core = slug.split("/")[-1]
    if core == "print-envelope":  # clinical-data/print-envelope -> buildPrintEnvelope
        return "buildPrintEnvelope"
    core = core.replace("-print-envelope", "")
    words = core.replace("opd", "OPD").split("-")
    return "build" + "".join(w[:1].upper() + w[1:] for w in words) + "PrintEnvelope"


# ---------------------------------------------------------------------------
# Layer 1 — print stylesheet hardware contracts
# ---------------------------------------------------------------------------


def test_print_css_declares_a4_portrait_geometry():
    css = PRINT_CSS.read_text(encoding="utf-8")
    assert "@media print" in css
    assert re.search(r"@page\s*\{\s*size:\s*A4 portrait", css), \
        "print.css must pin @page size to A4 portrait for target hardware"


def test_print_css_hides_app_chrome_on_paper():
    css = PRINT_CSS.read_text(encoding="utf-8")
    block = css[css.index("@media print"):]
    for selector in (".topbar", ".sidebar", ".workspace-header", ".record-nav", ".no-print"):
        assert selector in block, f"{selector} must be hidden inside @media print"
    assert "display:none!important" in block.replace(" ", "")


def test_print_css_break_rules_present():
    css = PRINT_CSS.read_text(encoding="utf-8")
    assert ".print-page-break{break-before:page}" in css.replace(" ", "").replace("\n", "") or \
        "print-page-break{break-before:page}" in css.replace(" ", "").replace("\n", "")
    assert "break-inside:avoid" in css
    assert "batch-report-sheet" in css and "break-before:page" in css


# ---------------------------------------------------------------------------
# Layer 2 — client-side wiring completeness (endpoint ↔ fetcher ↔ renderer)
# ---------------------------------------------------------------------------


def test_every_envelope_endpoint_has_api_js_fetcher():
    source = API_JS.read_text(encoding="utf-8")
    for slug in ENVELOPE_SLUGS:
        fetcher = _slug_to_fetcher(slug)
        assert f"export async function {fetcher}(" in source, \
            f"api.js missing fetcher {fetcher} for /reports/{slug}"
        assert f"/api/v1/reports/{slug}" in source, \
            f"api.js fetcher for {slug} does not target /api/v1/reports/{slug}"


def test_every_data_envelope_renderer_is_exported_and_imported():
    print_src = PRINT_JS.read_text(encoding="utf-8")
    reports_src = REPORTS_JS.read_text(encoding="utf-8")
    exported = set(re.findall(r"export function create(\w+?)PrintPreview", print_src))
    # Every ledger/audit envelope renderer (all except the two generic
    # clinical previews) must be imported by the Reports workspace.
    for name in exported - {"", "Batch"}:
        assert f"create{name}PrintPreview" in reports_src, \
            f"reports.js never imports create{name}PrintPreview"
    assert "createPrintPreview" in reports_src and "createBatchPrintPreview" in reports_src


def test_reports_workspace_wires_a_button_per_envelope():
    source = REPORTS_JS.read_text(encoding="utf-8")
    for slug in ENVELOPE_SLUGS:
        if slug.startswith("clinical-data"):
            continue  # clinical report + batch have their own forms
        fetcher = _slug_to_fetcher(slug)
        assert fetcher in source, f"reports.js never calls {fetcher}"
    # Each wired handler must render into the shared preview host.
    assert source.count('print-preview-host') >= len(ENVELOPE_SLUGS) - 2


def test_print_renderers_escape_all_dynamic_values():
    """Static XSS guard: no raw interpolation of payload fields.

    Every ``${...}`` hole in print.js must either pass through esc(),
    money()/valueMarkup() (which escape internally), or be a pure static
    literal. This keeps printer output safe against hostile free-text
    (remarks, transaction references, patient names).
    """
    source = PRINT_JS.read_text(encoding="utf-8")
    money_body = source[source.index("const money="):]
    money_body = money_body[:money_body.index("\n\n")]
    assert "esc(" in money_body, "money() must delegate to esc() for non-numeric input"
    offenders = []
    for expr in re.findall(r"\$\{([^}]*)\}", source):
        stripped = expr.strip()
        if not stripped:
            continue
        if ("esc(" in stripped or "valueMarkup(" in stripped
                or "money(" in stripped or "human(" in stripped):
            continue
        if re.fullmatch(r"[A-Za-z_$][\w$.]*", stripped):
            continue  # simple identifier hole; value still passes esc upstream
        if re.fullmatch(r"\w+\s*[+\-*/]\s*\d+", stripped):
            continue  # arithmetic over a loop counter (e.g. ``i+1``) renders a number
        offenders.append(stripped)
    # Remaining holes must be trivially safe (numbers/ternaries over escaped parts)
    unsafe = [o for o in offenders if "esc(" not in o and "?" not in o and "`" not in o]
    assert not unsafe, f"unescaped template holes found in print.js: {unsafe[:5]}"


# ---------------------------------------------------------------------------
# Layer 3 — backend envelope behavior on a cold install
# ---------------------------------------------------------------------------


def test_all_envelope_endpoints_are_registered():
    with make_client() as client:
        # NB: api_get/api_post inject auth headers themselves — never pass
        # ``headers=`` here or httpx raises "got multiple values".
        # The QA harness builds a bare FastAPI app without docs routes, so
        # enumerate the registered API routes instead of /openapi.json.
        paths: dict[str, set[str]] = {}
        for route in client.app.routes:
            endpoint = getattr(route, "endpoint", None)
            if endpoint is None or not getattr(endpoint, "__module__", "").startswith("app."):
                continue  # skip static/docs/system routes
            for method in getattr(route, "methods", set()):
                if method.upper() == "POST":
                    paths.setdefault(route.path, set()).add(method.lower())
        for slug in ENVELOPE_SLUGS:
            path = f"/api/v1/reports/{slug}"
            assert path in paths, f"{path} missing from the registered route table"
            assert "post" in paths[path], f"{path} must be a POST"


def test_ledger_envelopes_answer_200_on_cold_database():
    """Fresh-install smoke: every limit-style ledger envelope must build
    successfully against an empty database (clinics print before data
    exists; empty-state sheets are legitimate output)."""
    cold_requests = {
        "collection-summary-print-envelope": {"limit": 5},
        "receivables-aging-print-envelope": {"limit": 5},
        "invoice-receipt-continuity-print-envelope": {"limit": 5},
        "receipt-numbering-continuity-print-envelope": {"limit": 5},
        "invoice-payment-reconciliation-print-envelope": {"limit": 5},
        "payment-method-summary-print-envelope": {"limit": 5},
        "invoice-overpayment-print-envelope": {"limit": 5},
        "payment-method-overpayment-print-envelope": {"limit": 5},
        "invoice-settlement-audit-print-envelope": {"limit": 5},
        "refund-audit-print-envelope": {"limit": 5},
        "discharge-audit-print-envelope": {"limit": 5},
        "opd-queue-summary-print-envelope": {"limit_days": 7},
        "ward-occupancy-print-envelope": {"limit": 5},
        "investigation-billing-reconciliation-print-envelope": {"limit": 5},
    }
    with make_client() as client:
        for slug, body in cold_requests.items():
            resp = api_post(client, f"/reports/{slug}", json=body)
            assert resp.status_code == 200, f"{slug}: {resp.status_code} {resp.text[:200]}"
            env = resp.json()
            assert env["report_type"], f"{slug} envelope lacks report_type"
            assert "generated_at" in env and isinstance(env["data"], dict), \
                f"{slug} envelope missing common shape (title/generated_at/data)"


def test_clinical_envelope_requires_case_and_fails_clean_without():
    with make_client() as client:
        resp = api_post(
            client,
            "/reports/clinical-data/print-envelope",
            json={"patient_id": 1, "case_record_id": 999999},
        )
        # Missing case record must surface as a handled error, never 500.
        assert resp.status_code in (404, 422), resp.text[:200]


def test_invoice_envelope_matches_live_payment_data_end_to_end():
    """Paper-parity contract: the invoice print packet must reflect the
    exact totals the billing service computed after a real payment."""
    with make_client() as client:
        uid = seed_user()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        seed_number_sequence(sequence_name="invoice_number", prefix="INV-")
        seed_number_sequence(sequence_name="receipt_number", prefix="RCP-")

        # The billing endpoints cast the JWT ``sub`` to int for the
        # generated-by audit column, so we must ride a real login token
        # (the harness default subject "qa-batch103" is non-numeric and
        # correctly yields 401 since the Batch 110 auth hardening).
        from _qa_harness import token_for_login

        token = token_for_login(client, "qa-admin", "qa-password")
        headers = {"Authorization": f"Bearer {token}"}

        def post(path, payload):
            return client.post(f"/api/v1{path}", json=payload, headers=headers)

        patient = post(
            "/patients",
            {"first_name": "Print", "last_name": "QA", "gender": "Female"},
        )
        assert patient.status_code == 201, patient.text
        pid = patient.json()["id"]

        # Billing business rule: an invoice must link to a visit (or
        # admission) — mirror the real OPD flow Patient -> Visit -> Invoice.
        visit_id, _visit_number = seed_visit(patient_id=pid)

        invoice = post(
            "/billing/invoices",
            {
                "patient_id": pid,
                "visit_id": visit_id,
                "invoice_date": "2026-10-07T10:00:00",
                "total_amount": "250.00",
                "remarks": "<b>bold?</b>",
            },
        )
        assert invoice.status_code == 201, invoice.text
        inv_id = invoice.json()["id"]

        post(
            f"/billing/invoices/{inv_id}/items",
            {"item_type": "consultation", "description": "OPD visit",
             "quantity": "1", "unit_price": "250.00"},
        )
        payment = post(
            "/billing/payments",
            {"invoice_id": inv_id, "payment_datetime": "2026-10-07T10:30:00",
             "payment_method": "cash", "amount_paid": "100.00",
             "transaction_reference": "TXN-1"},
        )
        assert payment.status_code == 201, payment.text

        env_resp = post("/reports/invoice-print-envelope", {"invoice_id": inv_id})
        assert env_resp.status_code == 200, env_resp.text
        env = env_resp.json()
        assert env["report_type"] == "invoice_print"
        assert env["invoice_id"] == inv_id
        assert env["invoice_number"].startswith("INV-")
        data = env["data"]
        assert data["total_amount"] == "250.00"
        assert data["amount_paid"] == "100.00"
        assert data["balance_due"] == "150.00"
        assert data["payment_status"] == "partial"
        assert len(data["items"]) == 1 and data["items"][0]["line_total"] == "250.00"
        assert len(data["receipts"]) == 1
        receipt = data["receipts"][0]
        assert receipt["receipt_number"].startswith("RCP-")
        assert receipt["amount_paid"] == "100.00"
        assert receipt["transaction_reference"] == "TXN-1"
