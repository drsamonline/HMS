import { getServerBaseUrl, getAccessToken, listPatients } from "./api.js";

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
