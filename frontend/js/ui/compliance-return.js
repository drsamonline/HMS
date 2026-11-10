/* The NCH monthly return, as a document.
 *
 * A return is something a hospital files. Filing four figures from four screens is
 * how one of them ends up from the wrong month, so this gathers them into one sheet
 * that prints as it is previewed.
 *
 * The QCI section is present and marked rather than left out. A section that is
 * missing looks like a section that passed.
 */

import { escapeHtml } from "./dialog.js";
import { errorState, loadingState } from "./states.js";

function token() {
  try {
    return localStorage.getItem("hhms_token") || localStorage.getItem("token") || "";
  } catch {
    return "";
  }
}

function dutyRow(duty) {
  const value = duty.available
    ? `<strong>${duty.value === null ? "—" : duty.value}</strong> <small>${escapeHtml(duty.unit)}</small>`
    : `<em class="print-empty">not recorded</em>`;
  return `
    <tr>
      <td>${escapeHtml(duty.label)}</td>
      <td class="compliance-standard">${escapeHtml(duty.standard)}</td>
      <td class="compliance-value">${value}</td>
    </tr>`;
}

/**
 * @param {HTMLElement} host
 * @param {{start?: string, end?: string}} period
 */
export async function renderComplianceReturn(host, period = {}) {
  host.innerHTML = loadingState({ label: "Assembling the return…" });

  const params = new URLSearchParams();
  if (period.start) params.set("start", period.start);
  if (period.end) params.set("end", period.end);

  let data;
  try {
    const response = await fetch(`/api/v1/indicators/nch-return?${params}`, {
      credentials: "same-origin",
      headers: token() ? { Authorization: `Bearer ${token()}` } : {},
    });
    if (!response.ok) throw new Error(`The server answered ${response.status}.`);
    data = await response.json();
  } catch (error) {
    host.innerHTML = errorState({ message: error.message });
    return;
  }

  host.innerHTML = `
    <section class="print-preview-shell">
      <div class="print-toolbar no-print">
        <div><strong>${escapeHtml(data.title)}</strong><span class="print-count">${escapeHtml(data.period.start)} to ${escapeHtml(data.period.end)}</span></div>
        <div class="button-row"><button id="return-print">Print</button></div>
      </div>
      <article class="print-document">
        <header class="print-header">
          <div class="print-brand">HHMS</div>
          <div>
            <h1>${escapeHtml(data.title)}</h1>
            <p class="print-generated">${escapeHtml(data.period.start)} to ${escapeHtml(data.period.end)}</p>
          </div>
        </header>
        <section class="print-section" data-print-section="duties">
          <div class="print-section-heading"><h2>NCH duties</h2></div>
          <table class="rx-items-table">
            <thead><tr><th>Duty</th><th>Standard</th><th>Value</th></tr></thead>
            <tbody>${data.duties.map(dutyRow).join("")}</tbody>
          </table>
        </section>
        <section class="print-section" data-print-section="qci">
          <div class="print-section-heading"><h2>QCI measures</h2></div>
          <p>${escapeHtml(data.qci.note)}</p>
          <ul class="compliance-gaps">
            ${data.qci.gaps
              .map((gap) => `<li><strong>${escapeHtml(gap.name)}</strong> — ${escapeHtml(gap.reason)}</li>`)
              .join("")}
          </ul>
        </section>
      </article>
    </section>`;

  const printButton = host.querySelector("#return-print");
  if (printButton) printButton.addEventListener("click", () => window.print());
}
