/* Tick boxes for one person's permissions.
 *
 * A list of forty checkboxes answers "what can they do". It does not answer "why is
 * this one ticked", which is the question that matters when somebody leaves, or when
 * an auditor asks who could see the money. So every row says where its permission came
 * from: the role, or a grant somebody made by hand.
 *
 * A role permission is shown ticked and disabled. That is not a limitation to work
 * around - removing what a role gives is done by changing the role, so the change is
 * visible to everybody it affects rather than hidden in one person's screen.
 */

import { escapeHtml, notify } from "./dialog.js";
import { errorState, loadingState } from "./states.js";

function headers() {
  let token = "";
  try {
    token = localStorage.getItem("hhms_token") || localStorage.getItem("token") || "";
  } catch {
    token = "";
  }
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function load(userId) {
  const response = await fetch(`/api/v1/users/${userId}/permissions`, {
    credentials: "same-origin",
    headers: headers(),
  });
  if (!response.ok) throw new Error(`The server answered ${response.status}.`);
  return response.json();
}

function groupByModule(permissions) {
  const groups = new Map();
  for (const permission of permissions) {
    if (!groups.has(permission.module)) groups.set(permission.module, []);
    groups.get(permission.module).push(permission);
  }
  return groups;
}

function rowMarkup(permission) {
  const fromRole = permission.source === "role";
  const manual = permission.source === "manual";
  const badge = fromRole
    ? '<span class="perm-badge perm-role">role</span>'
    : manual
      ? '<span class="perm-badge perm-manual">granted</span>'
      : "";

  const expiry = permission.expires_at
    ? `<small class="perm-expiry">until ${escapeHtml(permission.expires_at.slice(0, 10))}</small>`
    : "";
  const reason = permission.reason
    ? `<small class="perm-reason">${escapeHtml(permission.reason)}</small>`
    : "";

  return `
    <label class="perm-row${fromRole ? " perm-from-role" : ""}">
      <input type="checkbox"
             data-code="${escapeHtml(permission.code)}"
             ${permission.granted ? "checked" : ""}
             ${fromRole ? "checked disabled" : ""}>
      <span class="perm-name">${escapeHtml(permission.name)} ${badge}</span>
      <span class="perm-desc">${escapeHtml(permission.description)}</span>
      ${expiry}${reason}
    </label>`;
}

/**
 * Render the permission editor for one user.
 *
 * @param {HTMLElement} host
 * @param {number} userId
 */
export async function renderPermissionEditor(host, userId) {
  host.innerHTML = loadingState({ label: "Reading permissions…" });

  let data;
  try {
    data = await load(userId);
  } catch (error) {
    host.innerHTML = errorState({ message: error.message });
    return;
  }

  const groups = groupByModule(data.permissions);

  host.innerHTML = `
    <section class="perm-panel">
      <header class="perm-header">
        <h2>Permissions</h2>
        <p>
          <strong>${data.from_role.length}</strong> from the role,
          <strong>${data.from_manual.length}</strong> granted by hand.
        </p>
      </header>

      <div class="perm-quick">
        <label>Grant for
          <select id="perm-expiry">
            <option value="">No expiry</option>
            <option value="7">a week</option>
            <option value="30">a month</option>
            <option value="90">three months</option>
          </select>
        </label>
        <label>Reason <input id="perm-reason" type="text" placeholder="locum cover, annual leave…"></label>
      </div>

      ${[...groups.entries()]
        .map(
          ([module, permissions]) => `
        <fieldset class="perm-group">
          <legend>${escapeHtml(module)}</legend>
          ${permissions.map(rowMarkup).join("")}
        </fieldset>`
        )
        .join("")}

      <footer class="perm-footer">
        <p>${escapeHtml(data.note)}</p>
        <button type="button" id="perm-save">Save</button>
      </footer>
    </section>`;

  host.querySelector("#perm-save").addEventListener("click", async () => {
    // Only the enabled boxes are the manual set. A disabled box is the role's, and
    // sending it would turn a role permission into a grant.
    const codes = [...host.querySelectorAll("input[data-code]:not(:disabled)")]
      .filter((box) => box.checked)
      .map((box) => box.dataset.code);

    const days = host.querySelector("#perm-expiry").value;
    const reason = host.querySelector("#perm-reason").value.trim();

    const response = await fetch(`/api/v1/users/${userId}/permissions`, {
      method: "PUT",
      credentials: "same-origin",
      headers: headers(),
      body: JSON.stringify({
        codes,
        expires_at: days
          ? new Date(Date.now() + Number(days) * 86400000).toISOString()
          : null,
        reason: reason || null,
      }),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      notify(detail?.detail || `Could not save: the server answered ${response.status}.`, {
        tone: "error",
      });
      return;
    }

    notify("Saved.", { tone: "success" });
    await renderPermissionEditor(host, userId);
  });
}
