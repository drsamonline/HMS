/* The landing screen.
 *
 * Rendered from what the server sends, so adding a role's home is a backend change
 * and not a frontend one. The panels use the component kit, which means the loading
 * and error states come for free rather than being written again here.
 */

import { errorState, loadingState } from "./ui/states.js";
import { escapeHtml } from "./ui/dialog.js";

function token() {
  try {
    return localStorage.getItem("hhms_token") || localStorage.getItem("token") || "";
  } catch {
    return "";
  }
}

function panelMarkup(panel) {
  const description = panel.description
    ? `<p class="home-panel-description">${escapeHtml(panel.description)}</p>`
    : "";

  if (panel.kind === "metrics") {
    return `
      <article class="home-panel home-panel-metrics" data-panel-source="${escapeHtml(panel.source || "")}">
        <h3>${escapeHtml(panel.title)}</h3>
        ${description}
        <div class="home-metrics" data-metrics>${loadingState({ label: "Reading…" })}</div>
      </article>`;
  }

  return `
    <article class="home-panel" data-panel-view="${escapeHtml(panel.view || "")}">
      <h3>${escapeHtml(panel.title)}</h3>
      ${description}
      <button class="secondary" data-open-view="${escapeHtml(panel.view || "")}">Open</button>
    </article>`;
}

/**
 * Render the home screen into a host element.
 *
 * @param {HTMLElement} host
 * @param {(view: string) => void} openView called when a shortcut is used
 */
export async function renderHome(host, openView) {
  host.innerHTML = loadingState({ label: "Opening your workspace…" });

  let home;
  try {
    const response = await fetch("/api/v1/home", {
      credentials: "same-origin",
      headers: token() ? { Authorization: `Bearer ${token()}` } : {},
    });
    if (!response.ok) throw new Error(`The server answered ${response.status}.`);
    home = await response.json();
  } catch (error) {
    host.innerHTML = errorState({ message: error.message });
    return;
  }

  host.innerHTML = `
    <section class="home">
      <header class="home-header">
        <h2>${escapeHtml(home.title)}</h2>
        <p>${escapeHtml(home.subtitle)}</p>
      </header>
      <div class="home-panels">
        ${home.panels.map(panelMarkup).join("")}
      </div>
    </section>`;

  host.querySelectorAll("[data-open-view]").forEach((button) => {
    button.addEventListener("click", () => openView(button.dataset.openView));
  });
}
