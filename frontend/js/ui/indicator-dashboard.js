/* The indicator dashboard.
 *
 * Renders what the server sends, grouped by the catalogue's own groups. No indicator
 * is named in this file: adding one is a backend change, which is the whole point of
 * the spine.
 *
 * The "no data" case is rendered as its own thing rather than as a zero, because a
 * dashboard full of false zeroes is worse than a dashboard that admits it is empty.
 */

import { escapeHtml } from "./dialog.js";
import { errorState, loadingState } from "./states.js";
import { sparkline } from "./sparkline.js";

function token() {
  try {
    return localStorage.getItem("hhms_token") || localStorage.getItem("token") || "";
  } catch {
    return "";
  }
}

function formatValue(row) {
  if (!row.available) return `<span class="ind-value ind-value-empty">no data</span>`;
  const value = row.value;
  if (row.unit === "percent") return `<span class="ind-value">${value.toFixed(1)}<small>%</small></span>`;
  if (row.unit === "ratio") return `<span class="ind-value">${value.toFixed(2)}</span>`;
  return `<span class="ind-value">${Math.round(value).toLocaleString()}</span>`;
}

function card(row, series) {
  return `
    <article class="ind-card" data-indicator="${escapeHtml(row.code)}">
      <header>
        <h3>${escapeHtml(row.name)}</h3>
        ${row.standard ? `<span class="ind-standard">${escapeHtml(row.standard)}</span>` : ""}
      </header>
      ${formatValue(row)}
      <div class="ind-trend">${series ? sparkline(series) : ""}</div>
      <p class="ind-definition">
        <span class="ind-num">${escapeHtml(row.numerator)}</span>
        ${row.denominator !== "count" ? `<span class="ind-den">÷ ${escapeHtml(row.denominator)}</span>` : ""}
      </p>
    </article>`;
}

/**
 * @param {HTMLElement} host
 * @param {{months?: number}} options
 */
export async function renderIndicatorDashboard(host, options = {}) {
  const months = options.months || 6;
  host.innerHTML = loadingState({ label: "Reading the indicators…" });

  const headers = token() ? { Authorization: `Bearer ${token()}` } : {};

  let rows;
  try {
    const [catalogue, values] = await Promise.all([
      fetch("/api/v1/indicators/catalogue", { credentials: "same-origin", headers }).then(
        (response) => response.json()
      ),
      fetch("/api/v1/indicators", { credentials: "same-origin", headers }).then((response) => {
        if (!response.ok) throw new Error(`The server answered ${response.status}.`);
        return response.json();
      }),
    ]);

    const trends = await Promise.all(
      values.map((row) =>
        fetch(`/api/v1/indicators/${encodeURIComponent(row.code)}/series?months=${months}`, {
          credentials: "same-origin",
          headers,
        })
          .then((response) => (response.ok ? response.json() : null))
          .catch(() => null)
      )
    );

    rows = values.map((row, index) => ({
      ...row,
      group_label:
        (catalogue.find((entry) => entry.code === row.code) || {}).group_label || row.group,
      series: trends[index],
    }));
  } catch (error) {
    host.innerHTML = errorState({ message: error.message });
    return;
  }

  const groups = new Map();
  rows.forEach((row) => {
    if (!groups.has(row.group)) groups.set(row.group, { label: row.group_label, rows: [] });
    groups.get(row.group).rows.push(row);
  });

  host.innerHTML = `
    <section class="ind-dashboard">
      <header class="ind-header">
        <div>
          <h2>Indicators</h2>
          <p>Every number with its definition, so it can be checked rather than trusted.</p>
        </div>
        <label class="ind-period">Trend over
          <select id="ind-months">
            ${[3, 6, 12]
              .map((option) => `<option value="${option}"${option === months ? " selected" : ""}>${option} months</option>`)
              .join("")}
          </select>
        </label>
      </header>
      ${[...groups.values()]
        .map(
          (group) => `
        <section class="ind-group">
          <h3 class="ind-group-title">${escapeHtml(group.label)}</h3>
          <div class="ind-cards">${group.rows.map((row) => card(row, row.series)).join("")}</div>
        </section>`
        )
        .join("")}
    </section>`;

  const select = host.querySelector("#ind-months");
  if (select) {
    select.addEventListener("change", () =>
      renderIndicatorDashboard(host, { months: Number(select.value) })
    );
  }
}
