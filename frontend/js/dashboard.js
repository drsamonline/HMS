import { getServerBaseUrl, getAccessToken, listPatients, getDashboardDueFollowups, getDashboardOutstandingInvoices, getDashboardBedOccupancy, getDashboardPendingInvestigations, getDashboardDischargeAudit, getDashboardOPDQueueSummary, getDashboardInvestigationBillingReconciliation } from "./api.js";

const $ = (s, r = document) => r.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>'"]/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" }[c]));

export async function openDashboard(host, context = {}) {
  host.innerHTML = `
    <section class="content-panel">
      <div class="module-head">
        <h2>HHMS Dashboard</h2>
        <p>Quick access to the hospital client workspace.</p>
      </div>
      <div id="dashboard-status" class="status-box">Loading dashboard…</div>
      <div class="dashboard-grid">
        <button type="button" class="dashboard-card" data-action="patients">
          <strong>Patients</strong><span>Search, register and open patient records.</span>
        </button>
        <button type="button" class="dashboard-card" data-action="statistics">
          <strong>Statistics</strong><span>View hospital, department and service statistics.</span>
        </button>
        <button type="button" class="dashboard-card" data-action="reports">
          <strong>Reports & Printing</strong><span>Prepare, preview and print clinical reports.</span>
        </button>
      </div>
    </section>
    <section class="content-panel">
      <h3>Due follow-ups (next 7 days)</h3>
      <div id="dashboard-due-followups" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>Outstanding invoices</h3>
      <div id="dashboard-outstanding-invoices" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>IPD bed occupancy</h3>
      <div id="dashboard-bed-occupancy" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>Pending investigations</h3>
      <div id="dashboard-pending-investigations" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>Discharge audit</h3>
      <div id="dashboard-discharge-audit" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>OPD queue daily summary</h3>
      <div id="dashboard-opd-queue-summary" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>Investigation billing reconciliation</h3>
      <div id="dashboard-investigation-billing" class="patient-list"><div class="empty-state">Loading…</div></div>
    </section>
    <section class="content-panel">
      <h3>Recent patients</h3>
      <div id="dashboard-recent" class="patient-list"></div>
    </section>
    <section class="content-panel">
      <h3>Server</h3>
      <div class="details">
        <p><strong>Endpoint:</strong> ${esc(getServerBaseUrl() || "Not connected")}</p>
        <p><strong>Session:</strong> ${getAccessToken() ? "Authenticated" : "Not authenticated"}</p>
      </div>
    </section>
  `;

  host.querySelectorAll("[data-action]").forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.action;
      document.querySelector(`.nav-item[data-app-view="${target}"]`)?.click();
      if (target === "patients") document.querySelector(".nav-item[data-view='patients']")?.click();
    });
  });

  try {
    const due = await getDashboardDueFollowups({ daysAhead: 7, limit: 20 });
    const dueHost = $("#dashboard-due-followups", host);
    const items = due?.items ?? [];
    if (!items.length) {
      dueHost.innerHTML = '<div class="empty-state">No follow-ups due in the next 7 days.</div>';
    } else {
      dueHost.innerHTML = items.map(f => `
        <button type="button" class="patient-card" data-followup-patient="${esc(f.patient_id)}">
          <strong>${esc(f.patient_name)}</strong>
          <span>${esc(f.case_number || "—")} · ${esc(new Date(f.next_followup_datetime).toLocaleString())}</span>
        </button>
      `).join("");
      dueHost.querySelectorAll("[data-followup-patient]").forEach(btn => {
        btn.addEventListener("click", () => {
          window.dispatchEvent(new CustomEvent("hhms:open-patient-clinical", { detail: { patientId: Number(btn.dataset.followupPatient) } }));
        });
      });
    }
  } catch {
    $("#dashboard-due-followups", host).innerHTML = '<div class="empty-state">Due follow-ups are unavailable right now.</div>';
  }

  try {
    const outstanding = await getDashboardOutstandingInvoices({ limit: 20 });
    const outstandingHost = $("#dashboard-outstanding-invoices", host);
    const invoices = outstanding?.items ?? [];
    if (!invoices.length) {
      outstandingHost.innerHTML = '<div class="empty-state">No outstanding invoices.</div>';
    } else {
      const money = v => Number(v ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      outstandingHost.innerHTML = `
        <p class="muted">${esc(invoices.length)} invoice(s) · total outstanding ${money(outstanding?.total_outstanding)}</p>
      ` + invoices.map(inv => `
        <button type="button" class="patient-card" data-outstanding-patient="${esc(inv.patient_id)}">
          <strong>${esc(inv.patient_name)}</strong>
          <span>${esc(inv.invoice_number)} · balance ${money(inv.balance_due)} of ${money(inv.total_amount)} · ${esc(inv.days_outstanding)} day(s) old</span>
        </button>
      `).join("");
      outstandingHost.querySelectorAll("[data-outstanding-patient]").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelector(".nav-item[data-view='patients']")?.click();
          window.dispatchEvent(new CustomEvent("hhms:open-patient", { detail: { patientId: Number(btn.dataset.outstandingPatient) } }));
        });
      });
    }
  } catch {
    $("#dashboard-outstanding-invoices", host).innerHTML = '<div class="empty-state">Outstanding invoices are unavailable right now.</div>';
  }

  try {
    const occupancy = await getDashboardBedOccupancy({ limit: 50 });
    const occupancyHost = $("#dashboard-bed-occupancy", host);
    const beds = occupancy?.items ?? [];
    if (!beds.length) {
      occupancyHost.innerHTML = '<div class="empty-state">No beds are currently occupied.</div>';
    } else {
      occupancyHost.innerHTML = `
        <p class="muted">${esc(occupancy?.occupied_count ?? 0)} of ${esc(occupancy?.total_beds ?? 0)} listed bed(s) occupied</p>
      ` + beds.map(bed => `
        <button type="button" class="patient-card" ${bed.patient_id ? `data-occupancy-patient="${esc(bed.patient_id)}"` : "disabled"}>
          <strong>${esc(bed.bed_number)}${bed.ward ? " · " + esc(bed.ward) : ""}</strong>
          <span>${bed.has_active_admission
            ? `${esc(bed.patient_name)} (${esc(bed.patient_number || "—")}) · ${esc(bed.admission_number || "—")} · ${esc(bed.length_of_stay_days)} day(s) admitted`
            : "Marked occupied but no active admission — check IPD records"}</span>
        </button>
      `).join("");
      occupancyHost.querySelectorAll("[data-occupancy-patient]").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelector(".nav-item[data-view='patients']")?.click();
          window.dispatchEvent(new CustomEvent("hhms:open-patient-clinical", { detail: { patientId: Number(btn.dataset.occupancyPatient) } }));
        });
      });
    }
  } catch {
    $("#dashboard-bed-occupancy", host).innerHTML = '<div class="empty-state">Bed occupancy is unavailable right now.</div>';
  }

  try {
    const pending = await getDashboardPendingInvestigations({ limit: 20 });
    const pendingHost = $("#dashboard-pending-investigations", host);
    const orders = pending?.items ?? [];
    if (!orders.length) {
      pendingHost.innerHTML = '<div class="empty-state">No investigations are awaiting results.</div>';
    } else {
      pendingHost.innerHTML = `
        <p class="muted">${esc(pending?.pending_count ?? 0)} pending · ${esc(pending?.in_progress_count ?? 0)} in progress</p>
      ` + orders.map(inv => `
        <button type="button" class="patient-card" data-pending-patient="${esc(inv.patient_id)}">
          <strong>${esc(inv.investigation_name)}</strong>
          <span>${esc(inv.patient_name)} (${esc(inv.patient_number || "—")}) · ${esc(inv.investigation_number)} · ${esc(inv.investigation_status)} · ${esc(inv.age_hours)} hour(s) old</span>
        </button>
      `).join("");
      pendingHost.querySelectorAll("[data-pending-patient]").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelector(".nav-item[data-view='patients']")?.click();
          window.dispatchEvent(new CustomEvent("hhms:open-patient-clinical", { detail: { patientId: Number(btn.dataset.pendingPatient) } }));
        });
      });
    }
  } catch {
    $("#dashboard-pending-investigations", host).innerHTML = '<div class="empty-state">Pending investigations are unavailable right now.</div>';
  }

  try {
    const audit = await getDashboardDischargeAudit({ limit: 50 });
    const auditHost = $("#dashboard-discharge-audit", host);
    const discharges = audit?.items ?? [];
    if (!discharges.length) {
      auditHost.innerHTML = '<div class="empty-state">No recent discharges to audit.</div>';
    } else {
      auditHost.innerHTML = `
        <p class="muted">${esc(audit?.total_discharges ?? 0)} discharge(s) · ${esc(audit?.reconciled_count ?? 0)} reconciled · ${esc(audit?.drift_count ?? 0)} drifted</p>
      ` + discharges.map(d => `
        <button type="button" class="patient-card" data-audit-patient="${esc(d.patient_id)}">
          <strong>${esc(d.patient_name)}${d.bed_number ? " · " + esc(d.bed_number) : ""}</strong>
          <span>${esc(d.discharge_number)} · ${esc(d.admission_number)} · ${d.is_reconciled
            ? `discharged ${esc(d.hours_since_discharge)} hour(s) ago`
            : !d.admission_discharged
              ? "Admission still active — check IPD records"
              : d.bed_id === null || d.bed_id === undefined
                ? "No bed link — check admission record"
                : "Bed still occupied — release it in IPD"}</span>
        </button>
      `).join("");
      auditHost.querySelectorAll("[data-audit-patient]").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelector(".nav-item[data-view='patients']")?.click();
          window.dispatchEvent(new CustomEvent("hhms:open-patient-clinical", { detail: { patientId: Number(btn.dataset.auditPatient) } }));
        });
      });
    }
  } catch {
    $("#dashboard-discharge-audit", host).innerHTML = '<div class="empty-state">Discharge audit is unavailable right now.</div>';
  }

  try {
    const queue = await getDashboardOPDQueueSummary({ limitDays: 14 });
    const queueHost = $("#dashboard-opd-queue-summary", host);
    const days = queue?.items ?? [];
    if (!days.length) {
      queueHost.innerHTML = '<div class="empty-state">No OPD queue activity in the reporting window.</div>';
    } else {
      queueHost.innerHTML = `
        <p class="muted">${esc(queue?.days_reported ?? 0)} day(s) · ${esc(queue?.total_tokens ?? 0)} token(s) · ${esc(queue?.total_open ?? 0)} open</p>
      ` + days.map(day => `
        <div class="patient-card">
          <strong>${esc(day.queue_date)}</strong>
          <span>${esc(day.total_tokens)} token(s) · waiting ${esc(day.waiting)} · in consultation ${esc(day.in_consultation)} · completed ${esc(day.completed)} · cancelled ${esc(day.cancelled)} · open ${esc(day.open_token_count)}</span>
        </div>
      `).join("");
    }
  } catch {
    $("#dashboard-opd-queue-summary", host).innerHTML = '<div class="empty-state">OPD queue summary is unavailable right now.</div>';
  }

  try {
    const invBilling = await getDashboardInvestigationBillingReconciliation({ limit: 50 });
    const invHost = $("#dashboard-investigation-billing", host);
    const orders = invBilling?.items ?? [];
    if (!orders.length) {
      invHost.innerHTML = '<div class="empty-state">No open investigations to reconcile against billing.</div>';
    } else {
      invHost.innerHTML = `
        <p class="muted">${esc(invBilling?.total_investigations_checked ?? 0)} open investigation(s) · ${esc(invBilling?.billed_count ?? 0)} billed · ${esc(invBilling?.billed_missing_count ?? 0)} unbilled · total billed ${esc(invBilling?.total_billed ?? "0")}</p>
      ` + orders.map(inv => `
        <button type="button" class="patient-card" data-invbilling-patient="${esc(inv.patient_id)}">
          <strong>${esc(inv.investigation_name)}${inv.is_billed_missing ? " · not billed" : ""}</strong>
          <span>${esc(inv.patient_name)} (${esc(inv.patient_number || "—")}) · ${esc(inv.investigation_number)} · ${esc(inv.investigation_status)} · ${esc(inv.age_hours)} hour(s) old · billed ${esc(inv.billed_amount)} (${esc(inv.invoice_item_count)} line(s))</span>
        </button>
      `).join("");
      invHost.querySelectorAll("[data-invbilling-patient]").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelector(".nav-item[data-view='patients']")?.click();
          window.dispatchEvent(new CustomEvent("hhms:open-patient-clinical", { detail: { patientId: Number(btn.dataset.invbillingPatient) } }));
        });
      });
    }
  } catch {
    $("#dashboard-investigation-billing", host).innerHTML = '<div class="empty-state">Investigation billing reconciliation is unavailable right now.</div>';
  }

  try {
    const recentIds = JSON.parse(sessionStorage.getItem("hhms.recent_patients") || "[]");
    const recent = [];
    for (const id of recentIds.slice(0, 5)) {
      try {
        const patients = await listPatients(String(id));
        const found = patients.find(p => String(p.id) === String(id)) || patients[0];
        if (found) recent.push(found);
      } catch {}
    }
    const recentHost = $("#dashboard-recent", host);
    if (!recent.length) {
      recentHost.innerHTML = '<div class="empty-state">No recently opened patients.</div>';
    } else {
      recentHost.innerHTML = recent.map(p => `
        <button type="button" class="patient-card" data-patient-id="${esc(p.id)}">
          <strong>${esc([p.first_name, p.middle_name, p.last_name].filter(Boolean).join(" ") || "Unnamed patient")}</strong>
          <span>${esc(p.patient_number || "—")} · ${esc(p.gender || "—")}</span>
        </button>
      `).join("");
      recentHost.querySelectorAll("[data-patient-id]").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelector(".nav-item[data-view='patients']")?.click();
          const search = document.querySelector("#patient-search");
          if (search) {
            search.value = "";
            search.dispatchEvent(new Event("input"));
          }
          window.dispatchEvent(new CustomEvent("hhms:open-patient", { detail: { patientId: Number(btn.dataset.patientId) } }));
        });
      });
    }
    $("#dashboard-status", host).textContent = "Dashboard ready.";
    $("#dashboard-status", host).className = "status-box success";
  } catch {
    $("#dashboard-status", host).textContent = "Dashboard loaded with limited recent-patient information.";
  }
}

__all__ = ["openDashboard"];
