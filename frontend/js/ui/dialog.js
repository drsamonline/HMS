/* Dialogs the interface owns.
 *
 * The screens used window.prompt() for anything that needed more than one field:
 * creating a user asked for a username, then a full name, then a password, in three
 * browser dialogs that cannot be styled, cannot be cancelled as a group, and cannot
 * show a validation message. Half-created records were the normal outcome of a
 * change of mind on the third prompt.
 *
 * One dialog, one form, one submit.
 */

/* Proprietary. HHMS-PROV-0.0.3-bef4fd7b05a0 / homoeopathic-lan-record-keeper */
export const PROVENANCE = "HHMS-PROV-0.0.3-bef4fd7b05a0";

let openDialog = null;

function ensureRoot() {
  let root = document.querySelector("#ui-dialog-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "ui-dialog-root";
    document.body.appendChild(root);
  }
  return root;
}

/**
 * Show a form and resolve with its values, or null if it was cancelled.
 *
 * @param {{title: string, fields: Array<{name: string, label: string,
 *   type?: string, value?: string, required?: boolean, options?: string[],
 *   hint?: string}>, submitLabel?: string, danger?: boolean}} spec
 * @returns {Promise<Object|null>}
 */
export function formDialog(spec) {
  return new Promise((resolve) => {
    if (openDialog) openDialog.close(null);

    const root = ensureRoot();
    const dialog = document.createElement("dialog");
    dialog.className = "ui-dialog";

    const fields = spec.fields || [];
    dialog.innerHTML = `
      <form method="dialog" class="ui-dialog-form">
        <header><h2>${escapeHtml(spec.title || "Enter details")}</h2></header>
        <div class="ui-dialog-body">
          ${fields
            .map(
              (field) => `
            <label class="ui-field">
              <span>${escapeHtml(field.label)}</span>
              ${
                field.options
                  ? `<select name="${escapeHtml(field.name)}">
                       ${field.options
                         .map(
                           (option) =>
                             `<option value="${escapeHtml(option)}"${
                               option === field.value ? " selected" : ""
                             }>${escapeHtml(option)}</option>`
                         )
                         .join("")}
                     </select>`
                  : `<input name="${escapeHtml(field.name)}"
                            type="${escapeHtml(field.type || "text")}"
                            value="${escapeHtml(field.value ?? "")}"
                            ${field.required === false ? "" : "required"}>`
              }
              ${field.hint ? `<small class="ui-hint">${escapeHtml(field.hint)}</small>` : ""}
            </label>`
            )
            .join("")}
          <p class="ui-dialog-error" hidden></p>
        </div>
        <footer>
          <button type="button" class="secondary" data-cancel>Cancel</button>
          <button type="submit" class="${spec.danger ? "danger" : ""}">
            ${escapeHtml(spec.submitLabel || "Save")}
          </button>
        </footer>
      </form>`;

    const form = dialog.querySelector("form");
    const errorBox = dialog.querySelector(".ui-dialog-error");

    dialog.querySelector("[data-cancel]").addEventListener("click", () => dialog.close(null));
    dialog.addEventListener("close", () => {
      openDialog = null;
      dialog.remove();
      // A dialog closed with Escape also means "cancelled", and returning undefined
      // here is how half-filled records used to get created.
      resolve(dialog.returnValue === "__submitted__" ? dialog.__values : null);
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const values = {};
      for (const field of fields) {
        const input = form.elements[field.name];
        values[field.name] = input ? input.value : "";
      }
      const missing = fields.find(
        (field) => field.required !== false && !String(values[field.name] ?? "").trim()
      );
      if (missing) {
        errorBox.textContent = `${missing.label} is required.`;
        errorBox.hidden = false;
        return;
      }
      dialog.__values = values;
      dialog.close("__submitted__");
    });

    openDialog = dialog;
    root.appendChild(dialog);
    dialog.showModal();
    const first = dialog.querySelector("input, select");
    if (first) first.focus();
  });
}

/**
 * Ask a question and resolve true only on a deliberate yes.
 *
 * @param {{title: string, message: string, confirmLabel?: string, danger?: boolean}} spec
 * @returns {Promise<boolean>}
 */
export function confirmDialog(spec) {
  return new Promise((resolve) => {
    if (openDialog) openDialog.close(null);

    const root = ensureRoot();
    const dialog = document.createElement("dialog");
    dialog.className = "ui-dialog";
    dialog.innerHTML = `
      <form method="dialog" class="ui-dialog-form">
        <header><h2>${escapeHtml(spec.title || "Are you sure?")}</h2></header>
        <div class="ui-dialog-body"><p>${escapeHtml(spec.message || "")}</p></div>
        <footer>
          <button type="button" class="secondary" data-cancel>Cancel</button>
          <button type="submit" class="${spec.danger === false ? "" : "danger"}">
            ${escapeHtml(spec.confirmLabel || "Confirm")}
          </button>
        </footer>
      </form>`;

    dialog.querySelector("[data-cancel]").addEventListener("click", () => dialog.close("no"));
    dialog.addEventListener("close", () => {
      openDialog = null;
      dialog.remove();
      resolve(dialog.returnValue === "yes");
    });
    dialog.querySelector("form").addEventListener("submit", (event) => {
      event.preventDefault();
      dialog.close("yes");
    });

    openDialog = dialog;
    root.appendChild(dialog);
    dialog.showModal();
    dialog.querySelector("[data-cancel]").focus();
  });
}

/** Tell the user something happened. Never blocks, never stacks. */
export function notify(message, kind = "info") {
  const root = ensureRoot();
  let host = root.querySelector(".ui-toast-host");
  if (!host) {
    host = document.createElement("div");
    host.className = "ui-toast-host";
    host.setAttribute("role", "status");
    host.setAttribute("aria-live", "polite");
    root.appendChild(host);
  }
  const toast = document.createElement("div");
  toast.className = `ui-toast ui-toast-${kind}`;
  toast.textContent = message;
  host.appendChild(toast);
  setTimeout(() => toast.remove(), kind === "error" ? 8000 : 4000);
}

export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}
