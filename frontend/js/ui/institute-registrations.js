/* The statutory register, as a screen rather than an API.
 *
 * Ten kinds of licence, most of which a given clinic does not need. The screen says
 * which two the law requires of an ordinary practice, and lets the rest be marked as
 * not applicable so the software stops asking.
 *
 * The point of it is the date. A register nobody opens is a list; a register with the
 * expiring ones at the top is a reminder, and a lapsed bio-medical waste authorisation
 * found during an inspection is the failure this exists to prevent.
 */

import { escapeHtml, formDialog, notify } from "./dialog.js";
import { errorState, loadingState } from "./states.js";

function token() {
  try {
    return localStorage.getItem("hhms_token") || localStorage.getItem("token") || "";
  } catch {
    return "";
  }
}

function headers() {
  const value = token();
  return {
    "Content-Type": "application/json",
    ...(value ? { Authorization: `Bearer ${value}` } : {}),
  };
}

const STATE_LABEL = {
  current: "Current",
  expiring: "Expiring soon",
  expired: "Expired",
  "not recorded": "Not recorded",
};

function rowMarkup(entry) {
  const state = STATE_LABEL[entry.state] || entry.state;
  const number = entry.number
    ? `<code>${escapeHtml(entry.number)}</code>`
    : `<span class="reg-missing">not recorded</span>`;
  const until = entry.valid_until ? escapeHtml(entry.valid_until.slice(0, 10)) : "—";

  return `
    <tr class="reg-row reg-${entry.state.replace(/\s/g, "-")}">
      <td>
        <strong>${escapeHtml(entry.label)}</strong>
        ${entry.required_by_default ? '<span class="reg-required">required</span>' : ""}
        <details><summary>What is this?</summary><p>${escapeHtml(entry.note)}</p></details>
      </td>
      <td>${number}</td>
      <td>${escapeHtml(entry.authority || "—")}</td>
      <td>${until}</td>
      <td><span class="reg-state">${escapeHtml(state)}</span></td>
      <td><button type="button" class="secondary" data-record="${escapeHtml(entry.kind)}">Record</button></td>
    </tr>`;
}

async function load() {
  const response = await fetch("/api/v1/institute/registrations", {
    credentials: "same-origin",
    headers: headers(),
  });
  if (!response.ok) throw new Error(`The server answered ${response.status}.`);
  return response.json();
}

async function record(kind, entry) {
  const values = await formDialog({
    title: entry ? `Record ${entry.label}` : "Record a registration",
    fields: [
      { name: "number", label: "Number", required: true, value: entry?.number || "" },
      { name: "authority", label: "Issued by", value: entry?.authority || "" },
      { name: "valid_until", label: "Valid until (leave blank if none)", type: "date" },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    submitLabel: "Save",
  });
  if (!values) return false;

  const payload = {
    number: values.number,
    authority: values.authority || null,
    valid_until: values.valid_until ? `${values.valid_until}T00:00:00Z` : null,
    notes: values.notes || null,
    applies: true,
  };

  const response = await fetch(`/api/v1/institute/registrations/${kind}`, {
    method: "PUT",
    credentials: "same-origin",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    notify(`Could not save: the server answered ${response.status}.`, { tone: "error" });
    return false;
  }
  notify("Recorded.", { tone: "success" });
  return true;
}

/**
 * Render the register into a host element.
 *
 * @param {HTMLElement} host
 */
export async function renderInstituteRegistrations(host) {
  host.innerHTML = loadingState({ label: "Reading the register…" });

  let report;
  try {
    report = await load();
  } catch (error) {
    host.innerHTML = errorState({ message: error.message });
    return;
  }

  const atRisk = report.at_risk || [];
  host.innerHTML = `
    <section class="reg-panel">
      <header class="reg-header">
        <div>
          <h2>Statutory registrations</h2>
          <p>${atRisk.length
            ? `<strong>${atRisk.length}</strong> need attention.`
            : "Everything recorded is current."}</p>
        </div>
      </header>
      <table class="reg-table">
        <thead>
          <tr><th>Registration</th><th>Number</th><th>Issued by</th><th>Valid until</th><th>State</th><th></th></tr>
        </thead>
        <tbody>${report.registrations.map(rowMarkup).join("")}</tbody>
      </table>
      <footer class="reg-footer"><p>${escapeHtml(report.note)}</p></footer>
    </section>`;

  host.querySelectorAll("[data-record]").forEach((button) => {
    button.addEventListener("click", async () => {
      const kind = button.dataset.record;
      const entry = report.registrations.find((item) => item.kind === kind);
      if (await record(kind, entry)) {
        await renderInstituteRegistrations(host);
      }
    });
  });
}
