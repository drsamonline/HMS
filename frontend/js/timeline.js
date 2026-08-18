import { listVisits, listAdmissions, listInvestigations, listInvoices, listPatientFiles, getPatientHistory, getPatientHistoryArchives } from "./api.js";

const esc = v => String(v ?? "").replace(/[&<>\'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c]));
const fmt = v => { if (!v) return "—"; const d = new Date(v); return Number.isNaN(d.getTime()) ? String(v) : d.toLocaleString(); };
const status = (el, msg, kind = "") => { el.textContent = msg; el.className = `status-box ${kind}`.trim(); };
const item = (date, type, title, meta, detail = "") => ({ date: new Date(date || 0), type, title, meta, detail });

export async function openPatientTimeline(box, patient) {
  box.innerHTML = `
    <div class="module-head"><div><h3>Patient Timeline</h3><p>Longitudinal history across live records and explicitly selected historical years.</p></div><button id="timeline-refresh" class="secondary">Refresh</button></div>
    <div class="form-grid"><label>Historical year<select id="timeline-year"><option value="">Select archived year</option></select></label><button id="timeline-load-year" class="secondary">Load Selected Year</button></div>
    <div id="timeline-status" class="status-box"></div><div id="timeline-summary" class="timeline-summary"></div><div id="timeline-list" class="timeline-list"></div>`;

  const st = box.querySelector("#timeline-status"), list = box.querySelector("#timeline-list"), summary = box.querySelector("#timeline-summary"), yearSelect = box.querySelector("#timeline-year");
  let selectedYears = [];

  async function loadArchives() {
    try {
      const data = await getPatientHistoryArchives(patient.id);
      const verified = (data?.archives || []).filter(a => a.verified);
      yearSelect.innerHTML = verified.length
        ? `<option value="">Select archived year</option>${verified.map(a => `<option value="${esc(a.year)}">${esc(a.year)} — ${esc(a.storage_tier)}</option>`).join("")}`
        : `<option value="">No verified historical archives available</option>`;
    } catch (e) {
      yearSelect.innerHTML = `<option value="">History unavailable</option>`;
      status(st, e?.message || "Unable to load historical years.", "error");
    }
  }

  async function loadLiveEvents() {
    const [visits, admissions, investigations, invoices, files] = await Promise.all([
      listVisits(patient.id), listAdmissions(patient.id), listInvestigations(patient.id), listInvoices(patient.id), listPatientFiles(patient.id),
    ]);
    return [
      ...(visits || []).map(v => item(v.visit_datetime, "OPD Visit", v.visit_number || "OPD Visit", `${v.visit_type || "OPD"} · ${v.consultation_status || "—"}`, v.chief_complaint || "")),
      ...(admissions || []).map(a => item(a.admission_datetime, "IPD Admission", a.admission_number || "Admission", `${a.admission_status || "—"} · Bed ${a.bed_id || "—"}`, a.admission_reason || "")),
      ...(investigations || []).map(x => item(x.requested_datetime || x.investigation_datetime, "Investigation", x.investigation_name || x.test_name || "Investigation", `${x.investigation_status || "—"} · ${x.fulfillment_mode || "—"}`, x.remarks || "")),
      ...(invoices || []).map(i => item(i.invoice_date, "Billing", i.invoice_number || "Invoice", `${i.status || "—"} · Total ${i.total_amount ?? "—"}`, i.notes || "")),
      ...(files || []).map(f => item(f.created_at, "MRD", f.file_no || "Patient File", `${f.file_type || "—"} · ${f.status || "—"}`, f.location || "")),
    ];
  }

  function render(events, historyCases = []) {
    const sorted = events.sort((a, b) => b.date - a.date);
    summary.innerHTML = `<div class="timeline-stat"><strong>${sorted.length}</strong><span>Timeline events</span></div><div class="timeline-stat"><strong>${historyCases.length}</strong><span>Historical cases loaded</span></div><div class="timeline-stat"><strong>${sorted.filter(e => e.type === "OPD Visit").length}</strong><span>OPD visits</span></div><div class="timeline-stat"><strong>${sorted.filter(e => e.type === "IPD Admission").length}</strong><span>Admissions</span></div>`;
    list.innerHTML = sorted.length ? sorted.map(e => `<article class="timeline-item"><div class="timeline-dot"></div><div class="timeline-card"><div class="timeline-top"><span class="timeline-type">${esc(e.type)}</span><time>${esc(fmt(e.date))}</time></div><h4>${esc(e.title)}</h4><p class="timeline-meta">${esc(e.meta)}</p>${e.detail ? `<p>${esc(e.detail)}</p>` : ""}</div></article>`).join("") : '<div class="empty-state">No clinical or administrative activity has been recorded for this patient yet.</div>';
  }

  async function load() {
    try {
      status(st, "Loading patient history…");
      const [liveEvents, history] = await Promise.all([loadLiveEvents(), getPatientHistory(patient.id, selectedYears)]);
      const cases = history?.cases || [];
      const caseEvents = cases.map(row => item(row.updated_at || row.created_at, row.source === "archive" ? "Historical Case" : "Current Case", row.case_number || "Case", `Year ${row.case_year} · ${row.storage_tier}${row.renewed_from_case_id ? ` · renewed from ${row.renewed_from_case_id}` : ""}`, row.case_status || ""));
      render([...liveEvents, ...caseEvents], cases.filter(row => row.source === "archive"));
      status(st, selectedYears.length ? `Live history plus ${selectedYears.length} selected archive year(s) loaded.` : "Live history loaded.", "success");
    } catch (e) { status(st, e?.message || "Unable to load patient history.", "error"); list.innerHTML = ""; }
  }

  box.querySelector("#timeline-refresh").addEventListener("click", load);
  box.querySelector("#timeline-load-year").addEventListener("click", async () => {
    const year = Number(yearSelect.value);
    if (!year) return;
    selectedYears = Array.from(new Set([...selectedYears, year]));
    await load();
  });

  await loadArchives();
  await load();
}
