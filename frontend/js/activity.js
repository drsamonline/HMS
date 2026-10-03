import { listAuditLogs, listServiceActivities } from "./api.js";

const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

export async function openActivityWorkspace(host, { patientId = null } = {}) {
  host.innerHTML = `<div class="content-card"><div class="workspace-header"><div><h2>Activity & Audit Trail</h2><p>Read-only operational history.</p></div><button id="activity-refresh" class="secondary">Refresh</button></div><div class="activity-grid"><section><h3>Service Activity</h3><div id="service-activity-list"></div></section><section><h3>Audit Log</h3><div id="audit-log-list"></div></section></div></div>`;
  const render = async () => {
    const [service, audit] = await Promise.all([listServiceActivities(patientId), listAuditLogs()]);
    host.querySelector("#service-activity-list").innerHTML = service.length ? service.map(x => `<article class="admin-list-item"><strong>${esc(x.status)}</strong><span>${esc(x.activity_datetime)} · ${esc(x.case_type)}</span><span>${esc(x.fulfillment_mode || "—")}</span><small>${esc(x.remarks || "")}</small></article>`).join("") : '<div class="empty-state">No service activity.</div>';
    host.querySelector("#audit-log-list").innerHTML = audit.length ? audit.map(x => `<article class="admin-list-item"><strong>${esc(x.activity)}</strong><span>${esc(x.entity_name)}${x.entity_id ? ` #${esc(x.entity_id)}` : ""}</span><small>${esc(x.action_timestamp)} · user ${esc(x.user_id)}</small><div>${esc(x.remarks || "")}</div></article>`).join("") : '<div class="empty-state">No audit entries.</div>';
  };
  host.querySelector("#activity-refresh").onclick = render;
  await render();
}
