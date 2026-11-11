/* The guided first run.
 *
 * Five steps, in the order a working day happens. Progress is read from the server,
 * so it survives a closed laptop and follows a person to another machine.
 *
 * The panel is dismissible and does not block anything: a tutorial that stands between
 * a receptionist and a queue is a tutorial that gets closed without reading.
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

function stepMarkup(step, index) {
  const state = step.done ? "done" : "todo";
  return `
    <li class="tutorial-step tutorial-step-${state}">
      <span class="tutorial-index">${step.done ? "✓" : index + 1}</span>
      <div class="tutorial-body">
        <strong>${escapeHtml(step.title)}</strong>
        <p class="tutorial-what">${escapeHtml(step.what)}</p>
        <p class="tutorial-why">${escapeHtml(step.why)}</p>
        ${step.done ? "" : `<button type="button" class="secondary" data-tutorial-view="${escapeHtml(step.view)}">Open ${escapeHtml(step.view)}</button>`}
      </div>
    </li>`;
}

/**
 * @param {HTMLElement} host
 * @param {(view: string) => void} openView
 */
export async function renderTutorial(host, openView) {
  host.innerHTML = loadingState({ label: "Checking what you have done…" });

  let data;
  try {
    const response = await fetch("/api/v1/tutorial", {
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
    <section class="tutorial">
      <header class="tutorial-header">
        <div>
          <h2>Getting started</h2>
          <p>${esc(data.completed)} of ${esc(data.total)} done. ${escapeHtml(data.note)}</p>
        </div>
        <button type="button" class="secondary" id="tutorial-dismiss">Hide</button>
      </header>
      ${data.finished
        ? `<p class="tutorial-finished">That is a full working day. Nothing here counted a real patient.</p>`
        : `<ol class="tutorial-steps">${data.steps.map(stepMarkup).join("")}</ol>`}
    </section>`;

  host.querySelectorAll("[data-tutorial-view]").forEach((button) => {
    button.addEventListener("click", () => openView(button.dataset.tutorialView));
  });
  host.querySelector("#tutorial-dismiss").addEventListener("click", () => {
    host.innerHTML = "";
    try {
      localStorage.setItem("hhms_tutorial_hidden", "1");
    } catch {
      /* a browser with no storage still gets a working Hide button */
    }
  });
}

/** True when the person has not hidden it and has not finished. */
export function tutorialVisible() {
  try {
    return localStorage.getItem("hhms_tutorial_hidden") !== "1";
  } catch {
    return true;
  }
}
