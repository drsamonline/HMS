import { listArchives, getHistoricalCases } from "./api.js";

const esc = v => String(v ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",""":"&quot;"}[c]));

export async function openHistoricalWorkspace(host, currentPatient = null) {
  host.innerHTML = `
    <section class="content-card">
      <header class="workspace-header"><div><h2>Historical Data</h2><p>Load archived case records by operational year without attaching old databases to normal live usage.</p></div></header>
      <div class="form-grid">
        <label>Operational year<select id="history-year"><option value="">Loading…</option></select></label>
        <label>Patient ID<input id="history-patient" type="number" min="1" value="${currentPatient?.id ?? ""}" placeholder="Patient ID"></label>
      </div>
      <div class="button-row"><button id="history-load">Load Historical Cases</button><button id="history-refresh" class="secondary">Refresh Archives</button></div>
      <div id="history-status" class="status-box"></div>
      <div id="history-results"></div>
    </section>`;
  const yearSelect = host.querySelector("#history-year");
  const patientInput = host.querySelector("#history-patient");
  const status = host.querySelector("#history-status");
  const results = host.querySelector("#history-results");
  async function loadArchives(){
    try {
      status.textContent = "Loading available archives…";
      const archives = await listArchives();
      const verified = archives.filter(a => a.verified);
      yearSelect.innerHTML = verified.length ? verified.map(a => `<option value="${a.archive_year}">${esc(a.archive_year)} — ${esc(a.storage_tier)}</option>`).join("") : `<option value="">No archives available</option>`;
      status.textContent = verified.length ? `${verified.length} verified archive(s) available.` : "No verified historical archives are available.";
      if (currentPatient?.id) await loadCases();
    } catch (e) { status.textContent = e instanceof Error ? e.message : "Unable to load archives."; status.className="status-box error"; }
  }
  async function loadCases(){
    const year = yearSelect.value; const pid = patientInput.value;
    if (!year || !pid) { results.innerHTML = `<div class="empty-state">Select an archived year and enter a patient ID.</div>`; return; }
    try {
      status.className="status-box"; status.textContent=`Loading ${year} historical cases…`;
      const rows = await getHistoricalCases(year, pid);
      results.innerHTML = rows.length ? rows.map(r => `<article class="admin-list-item"><strong>${esc(r.case_number)}</strong><span>Year ${esc(r.case_year)} · ${esc(r.case_status)}</span><span>Storage: ${esc(r.storage_tier)}</span><span>Updated: ${esc(r.updated_at)}</span></article>`).join("") : `<div class="empty-state">No historical case records found for this patient and year.</div>`;
      status.className="status-box success"; status.textContent=`${rows.length} historical case record(s) loaded.`;
    } catch (e) { status.className="status-box error"; status.textContent=e instanceof Error ? e.message : "Unable to load historical cases."; }
  }
  host.querySelector("#history-load").onclick=loadCases;
  host.querySelector("#history-refresh").onclick=loadArchives;
  await loadArchives();
}
