"""Batch 114 QA — Cross-module client integration polish contract.

Milestone 7 (Release) part 10 / Milestone 3 "role-aware UI" follow-through.
Locks the wiring introduced for the IPD Management workspace and the
Pharmacy authenticated-user-context fix across three verifiable layers:

* Static frontend contracts — nav button, RBAC access vocabulary, app.js
  routing/import, api.js fetchers, XSS escaping in every rendered template
  of the new module, and a syntax check of all touched ES modules.
* Backend round-trips over the exact routes the workspace calls: bed
  census create/list/filter/PATCH, admission create with bed-occupancy
  side effects, discharge releasing the bed, and the guard rails the forms
  rely on (occupied-bed rejection, unknown-patient rejection).
* RBAC gating semantics — administrator blanket access plus explicit
  permission matching against the ACCESS map, so the new nav item cannot
  be silently dead-gated.

Physical browser/printer interaction remains a field checklist; every
headlessly-verifiable invariant is asserted here.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _qa_harness import (  # noqa: E402
    api_get,
    api_patch,
    api_post,
    make_client,
    seed_number_sequence,
    seed_user,
)

PROJECT_ROOT = TESTS_DIR.parents[1]
FRONTEND = PROJECT_ROOT / "frontend"

INDEX_HTML = FRONTEND / "index.html"
APP_JS = FRONTEND / "js" / "app.js"
RBAC_JS = FRONTEND / "js" / "rbac.js"
API_JS = FRONTEND / "js" / "api.js"
IPD_MGMT_JS = FRONTEND / "js" / "ipd_management.js"
PHARMACY_JS = FRONTEND / "js" / "pharmacy.js"


def _now_iso() -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()


def _seed_ipd_sequences() -> None:
    """Admissions/discharges mint human-readable numbers server-side."""
    seed_number_sequence(sequence_name="admission_number", prefix="ADM-")
    seed_number_sequence(sequence_name="discharge_number", prefix="DIS-")


# ---------------------------------------------------------------------------
# Layer 1 — static frontend wiring contracts
# ---------------------------------------------------------------------------

def test_ipd_management_nav_button_registered():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'data-app-view="ipd-management"' in html
    assert 'data-access="ipd-management"' in html
    assert html.count('data-app-view="ipd-management"') == 1


def test_rbac_access_map_defines_ipd_management_key():
    src = RBAC_JS.read_text(encoding="utf-8")
    m = re.search(r'"ipd-management"\s*:\s*\[([^\]]+)\]', src)
    assert m, "ACCESS map missing ipd-management entry"
    perms = {p.strip().strip('"\'') for p in m.group(1).split(",")}
    assert {"beds.manage", "wards.manage", "admission.manage"} <= perms


def test_app_js_routes_ipd_management_view():
    src = APP_JS.read_text(encoding="utf-8")
    assert "openIPDManagementWorkspace" in src
    assert "./ipd_management.js" in src
    assert re.search(r'appView==="ipd-management"', src), \
        "workspace switch does not route to ipd-management"


def test_api_js_has_all_ipd_management_fetchers():
    src = API_JS.read_text(encoding="utf-8")
    for fn in ("listBeds", "createBed", "updateBed", "listAllAdmissions",
               "createAdmission", "updateAdmission", "getDischargeByAdmission",
               "createDischarge"):
        assert re.search(rf"export async function {fn}\b", src), \
            f"api.js missing fetcher {fn}"


def _template_interpolations(src: str) -> list[str]:
    """Return ${...} chunks with nested template literals stripped out.

    Naive ``[^}]*`` regexes truncate at the first inner brace (e.g.
    ``${b.room_number?` · ${b.room_number}`:""}``), so we scan with a
    small brace matcher instead.
    """
    chunks: list[str] = []
    i = 0
    while True:
        j = src.find("${", i)
        if j < 0:
            return chunks
        depth = 0
        k = j + 1  # at "{"
        while k < len(src):
            if src[k] == "{":
                depth += 1
            elif src[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        chunks.append(src[j + 2:k])
        i = k + 1


def test_ipd_management_workspace_escapes_all_dynamic_values():
    src = IPD_MGMT_JS.read_text(encoding="utf-8")
    assert "const esc=" in src, "no HTML-escape helper defined"
    offenders = [
        chunk for chunk in _template_interpolations(src)
        if re.search(
            r"\bb\.bed_number\b|\bb\.ward\b|\bb\.room_number\b|\ba\.admission_number\b"
            r"|\ba\.patient_id\b|\ba\.bed_id\b|\ba\.case_type\b|\ba\.admission_status\b",
            chunk,
        )
        and "esc(" not in chunk
    ]
    assert not offenders, f"unescaped interpolations: {offenders}"


def test_pharmacy_dispense_uses_authenticated_user_context():
    src = PHARMACY_JS.read_text(encoding="utf-8")
    assert "hhmsCurrentUserId" in src, \
        "pharmacy no longer reads the global authenticated user id"
    assert re.search(r"dispensed_by:state\.userId", src.replace(" ", "")), \
        "dispense payload not bound to state.userId"
    # Record Dispense stays disabled until a user id is available.
    assert re.search(r"data-ph-save[^$]*state\.userId", src)


def test_touched_frontend_modules_parse_as_es_modules():
    for js in (IPD_MGMT_JS, APP_JS, RBAC_JS, API_JS, PHARMACY_JS):
        probe = subprocess.run(
            ["node", "--input-type=module", "--eval", f"import('{js.as_uri()}')"],
            capture_output=True, text=True,
        )
        # Runtime failures (missing DOM etc.) are tolerated; SyntaxError is not.
        assert "SyntaxError" not in probe.stderr, \
            f"{js.name} has a syntax error: {probe.stderr[:400]}"


# ---------------------------------------------------------------------------
# Layer 2 — backend round-trips over the exact routes the workspace calls
# ---------------------------------------------------------------------------

def test_bed_census_round_trip_and_filters():
    with make_client():
        uid = seed_user()
        created = api_post("/beds", json={
            "bed_number": "QA-B1", "ward": "Ward A",
            "room_number": "R-1", "bed_type": "General",
        })
        assert created.status_code == 201, created.text
        bed = created.json()
        assert bed["occupancy_status"] == "available"

        listed = api_get("/beds", params={"ward": "Ward A"}).json()
        assert any(b["id"] == bed["id"] for b in listed)

        filtered = api_get(
            "/beds", params={"occupancy_status": "maintenance"}
        ).json()
        assert all(b["id"] != bed["id"] for b in filtered)

        patched = api_patch(f"/beds/{bed['id']}", json={
            "occupancy_status": "maintenance",
        })
        assert patched.status_code == 200, patched.text
        assert patched.json()["occupancy_status"] == "maintenance"


def test_admission_discharge_flow_with_bed_occupancy_side_effects():
    with make_client():
        uid = seed_user()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        _seed_ipd_sequences()

        patient = api_post("/patients", json={
            "first_name": "Integration", "last_name": "QA",
            "gender": "Male", "mobile_number": "9000000114",
        })
        assert patient.status_code == 201, patient.text
        pid = patient.json()["id"]

        bed = api_post("/beds", json={
            "bed_number": "QA-B2", "ward": "Ward B",
        }).json()

        adm = api_post("/admissions", json={
            "patient_id": pid, "bed_id": bed["id"],
            "admitted_by": uid, "admission_datetime": _now_iso(),
            "case_type": "new", "admission_reason": "QA admission",
        })
        assert adm.status_code == 201, adm.text
        admission = adm.json()
        assert admission["admission_status"] == "admitted"
        assert admission["admission_number"]

        # Bed flips to occupied (census filter the UI depends on).
        beds_after = api_get(
            "/beds", params={"occupancy_status": "occupied"}
        ).json()
        assert any(b["id"] == bed["id"] for b in beds_after)

        # Active-admission list used by the workspace refresh().
        active = api_get("/admissions", params={"status": "admitted"}).json()
        assert any(a["id"] == admission["id"] for a in active)

        dis = api_post("/discharges", json={
            "admission_id": admission["id"], "discharged_by": uid,
            "discharge_datetime": _now_iso(),
            "discharge_summary": "QA discharge",
        })
        assert dis.status_code == 201, dis.text
        assert dis.json()["discharge_number"]

        # Bed released back to available — exactly what the UI claims.
        beds_final = api_get("/beds").json()
        released = next(b for b in beds_final if b["id"] == bed["id"])
        assert released["occupancy_status"] == "available"


def test_admission_rejects_non_available_bed():
    with make_client():
        uid = seed_user()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        _seed_ipd_sequences()

        patient = api_post("/patients", json={
            "first_name": "Occupant", "last_name": "QA",
            "gender": "Female",
        }).json()
        bed = api_post("/beds", json={
            "bed_number": "QA-B3", "ward": "Ward C",
        }).json()
        first = api_post("/admissions", json={
            "patient_id": patient["id"], "bed_id": bed["id"],
            "admitted_by": uid, "admission_datetime": _now_iso(),
        })
        assert first.status_code == 201, first.text
        second = api_post("/admissions", json={
            "patient_id": patient["id"], "bed_id": bed["id"],
            "admitted_by": uid, "admission_datetime": _now_iso(),
        })
        assert second.status_code == 400, second.text
        assert "not available" in second.json()["detail"].lower()


def test_admission_rejects_unknown_patient():
    with make_client():
        _seed_ipd_sequences()
        uid = seed_user()
        bed = api_post("/beds", json={"bed_number": "QA-B4"}).json()
        resp = api_post("/admissions", json={
            "patient_id": 999999, "bed_id": bed["id"],
            "admitted_by": uid, "admission_datetime": _now_iso(),
        })
        assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# Layer 3 — RBAC gating semantics for the new workspace
# ---------------------------------------------------------------------------

def test_every_nav_access_key_including_ipd_management_has_vocabulary():
    index = INDEX_HTML.read_text(encoding="utf-8")
    rbac = RBAC_JS.read_text(encoding="utf-8")
    keys = set(re.findall(r'data-access="([^"]+)"', index))
    vocab = set(re.findall(r'^\s*(?:"(\w[\w-]*)"|(\w+))\s*:\s*\[', rbac,
                           re.MULTILINE))
    vocab = {a or b for a, b in vocab}
    missing = keys - vocab
    assert not missing, f"nav keys without ACCESS vocabulary: {sorted(missing)}"
    assert "ipd-management" in vocab


def test_rbac_gating_semantics_for_ipd_management(tmp_path):
    """Administrator blanket access + explicit permission matching via node."""
    harness = tmp_path / "gate.mjs"
    harness.write_text(
        "import {canAccess} from '" + RBAC_JS.as_uri() + "';\n"
        "const results = {\n"
        "  adminBlanket: canAccess({roles:['Admin'], permissions:[]}, 'ipd-management'),\n"
        "  explicitGrant: canAccess({roles:['Nurse'], permissions:['beds.manage']}, 'ipd-management'),\n"
        "  denied: canAccess({roles:['Nurse'], permissions:['patients.read']}, 'ipd-management'),\n"
        "  anonymous: canAccess(null, 'ipd-management'),\n"
        "};\n"
        "console.log(JSON.stringify(results));\n",
        encoding="utf-8",
    )
    probe = subprocess.run(
        ["node", str(harness)], capture_output=True, text=True, timeout=30,
    )
    assert probe.returncode == 0, probe.stderr
    import json as _json
    outcomes = _json.loads(probe.stdout.strip())
    assert outcomes == {
        "adminBlanket": True,
        "explicitGrant": True,
        "denied": False,
        "anonymous": False,
    }, outcomes
