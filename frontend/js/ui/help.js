/* The help a screen needs, without leaving the screen.
 *
 * The guidance already exists in the role guides and the operations runbook. What was
 * missing was having it where the person is, at the moment they are stuck, rather than
 * in a document nobody opens on a busy morning.
 *
 * The panel is a drawer rather than a page: leaving the screen to read about the screen
 * is how somebody loses the patient they were in the middle of registering.
 */

import { escapeHtml } from "./dialog.js";

function token() {
  try {
    return localStorage.getItem("hhms_token") || localStorage.getItem("token") || "";
  } catch {
    return "";
  }
}

/** Markdown-lite: paragraphs, bold, inline code and bullets. Enough for four paragraphs. */
function render(text) {
  const blocks = text.split(/\n{2,}/);
  return blocks
    .map((block) => {
      const lines = block.split("\n").filter(Boolean);
      if (lines.every((line) => line.startsWith("- "))) {
        return `<ul>${lines
          .map((line) => `<li>${inline(line.slice(2))}</li>`)
          .join("")}</ul>`;
      }
      return `<p>${inline(lines.join(" "))}</p>`;
    })
    .join("");
}

function inline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

let panel = null;

function ensurePanel() {
  if (panel) return panel;
  panel = document.createElement("aside");
  panel.id = "help-panel";
  panel.className = "help-panel no-print";
  panel.setAttribute("role", "complementary");
  panel.setAttribute("aria-label", "Help for this screen");
  panel.hidden = true;
  document.body.appendChild(panel);
  return panel;
}

/**
 * Show the help for a screen.
 *
 * @param {string} view the screen the user is on
 */
export async function showHelp(view) {
  const host = ensurePanel();
  host.hidden = false;
  host.innerHTML = `<div class="help-loading">Reading…</div>`;

  let topic;
  try {
    const response = await fetch(`/api/v1/help/${encodeURIComponent(view)}`, {
      credentials: "same-origin",
      headers: token() ? { Authorization: `Bearer ${token()}` } : {},
    });
    if (response.status === 404) {
      host.innerHTML = `
        <header class="help-header"><h2>No help for this screen</h2>
          <button class="secondary" data-help-close>Close</button></header>
        <div class="help-body"><p>This screen has no help text yet. The role guides in
        <code>docs/roles/</code> cover what you are likely to need.</p></div>`;
      host.querySelector("[data-help-close]").addEventListener("click", hideHelp);
      return;
    }
    if (!response.ok) throw new Error(`The server answered ${response.status}.`);
    topic = await response.json();
  } catch (error) {
    host.innerHTML = `
      <header class="help-header"><h2>Could not load help</h2>
        <button class="secondary" data-help-close>Close</button></header>
      <div class="help-body"><p>${escapeHtml(error.message)}</p></div>`;
    host.querySelector("[data-help-close]").addEventListener("click", hideHelp);
    return;
  }

  host.innerHTML = `
    <header class="help-header">
      <h2>${escapeHtml(topic.title)}</h2>
      <button class="secondary" data-help-close aria-label="Close help">Close</button>
    </header>
    <div class="help-body">${render(topic.body)}</div>
    <footer class="help-footer">
      <small>More: <code>docs/roles/</code> and <code>docs/OPERATIONS.md</code></small>
    </footer>`;

  host.querySelector("[data-help-close]").addEventListener("click", hideHelp);
}

export function hideHelp() {
  if (panel) {
    panel.hidden = true;
    panel.innerHTML = "";
  }
}

/** The "?" button a screen puts in its header. */
export function helpButton(view) {
  return `<button type="button" class="secondary help-button" data-help="${escapeHtml(view)}" aria-label="Help for this screen">?</button>`;
}

/** Wire any help buttons inside a host. Call after rendering a screen. */
export function bindHelpButtons(host) {
  host.querySelectorAll("[data-help]").forEach((button) => {
    button.addEventListener("click", () => showHelp(button.dataset.help));
  });
}
