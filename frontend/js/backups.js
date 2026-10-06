import { apiDelete, apiGet, apiPost } from "./api.js";

export async function openBackupWorkspace(host, profile = {}) {
  host.innerHTML = `<div class="module-header"><div><h2>Database Backups</h2><p>Administrator-managed local SQLite backups.</p></div><button class="secondary" data-backup-refresh>Refresh</button></div><div data-backup-status class="status-box"></div><section class="module-card"><div class="form-grid"><label>Optional backup name<input name="backup_name" data-backup-name maxlength="100" placeholder="hhms-backup-YYYYMMDD.sqlite3"></label><button class="primary" data-backup-create>Create Backup</button></div><div data-backup-list class="record-list"></div></section>`;
  const status = host.querySelector("[data-backup-status]");
  const list = host.querySelector("[data-backup-list]");
  const name = host.querySelector("[data-backup-name]");
  const setStatus = (msg, type = "") => { status.textContent = msg || ""; status.className = `status-box ${type}`.trim(); };
  async function load() {
    try {
      setStatus("Loading backups…");
      const rows = await apiGet("/maintenance/backups");
      list.innerHTML = rows.length ? rows.map(row => `<article class="record-row"><div><strong>${escapeHtml(row.name)}</strong><div>${Number(row.size_bytes || 0).toLocaleString()} bytes · ${escapeHtml(new Date(row.modified_at).toLocaleString())}</div></div><div class="button-row"><a class="button secondary" href="#" data-backup-download="${escapeAttr(row.name)}">Download</a><button class="secondary" data-backup-delete="${escapeAttr(row.name)}">Delete</button></div></article>`).join("") : '<div class="empty-state">No backups created yet.</div>';
      list.querySelectorAll("[data-backup-download]").forEach(a => a.addEventListener("click", async e => { e.preventDefault(); const response = await apiGet(`/maintenance/backups/${encodeURIComponent(a.dataset.backupDownload)}/download`, { rawResponse: true }); const url = URL.createObjectURL(await response.blob()); const link = document.createElement("a"); link.href = url; link.download = a.dataset.backupDownload; link.click(); URL.revokeObjectURL(url); }));
      list.querySelectorAll("[data-backup-delete]").forEach(btn => btn.addEventListener("click", async () => { if (!confirm(`Delete backup ${btn.dataset.backupDelete}?`)) return; await apiDelete(`/maintenance/backups/${encodeURIComponent(btn.dataset.backupDelete)}`); await load(); }));
      setStatus(rows.length ? `${rows.length} backup(s) available.` : "No backups created yet.", rows.length ? "success" : "");
    } catch (err) { setStatus(err instanceof Error ? err.message : "Unable to load backups.", "error"); }
  }
  host.querySelector("[data-backup-refresh]").addEventListener("click", load);
  host.querySelector("[data-backup-create]").addEventListener("click", async () => { try { setStatus("Creating backup…"); await apiPost("/maintenance/backups", { name: name.value.trim() || null }); name.value = ""; await load(); } catch (err) { setStatus(err instanceof Error ? err.message : "Unable to create backup.", "error"); } });
  await load();
}

function escapeHtml(value) { return String(value).replace(/[&<>"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[ch])); }
function escapeAttr(value) { return escapeHtml(value).replace(/'/g, "&#39;"); }
