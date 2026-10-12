// Local draft autosave (frontend "data draft saver").
//
// The server-side desktop console already snapshots the live database on
// shutdown; this module covers the *client* side of the same requirement:
//   * every keystroke in any form field is captured (input event delegation)
//     and persisted to localStorage per-form, so nothing entered is lost if
//     the tab/window closes unexpectedly ("save on every step");
//   * while a saved draft has not been submitted yet, the browser is asked to
//     warn on page close (beforeunload guard);
//   * when the GUI loses its connection to the HHMS server (network drop or
//     server exit), all currently visible forms are snapshotted immediately —
//     data typed up to that last step is always kept locally;
//   * on next load, forms with unsaved drafts are restored and a small banner
//     offers one-click "Discard all drafts" cleanup.
//
// Drafts are keyed by a stable identity for each form: an explicit
// data-draft-key attribute wins, otherwise the form id, otherwise the sorted
// list of field names.  Values are only ever stored locally — no patient data
// leaves the browser from this module.

const DRAFT_PREFIX = "hhms.draft.";
const DEBOUNCE_MS = 400;

let timer = null;
let bannerEl = null;

function formKey(form) {
  if (form.dataset && form.dataset.draftKey) return form.dataset.draftKey;
  if (form.id) return form.id;
  const fields = [...form.querySelectorAll("input[name],select[name],textarea[name]")]
    .map((el) => el.name)
    .sort()
    .join(",");
  return fields ? `anon:${fields}` : null;
}

function storageKey(key) {
  return DRAFT_PREFIX + key;
}

function serializeForm(form) {
  const data = {};
  form.querySelectorAll("input,select,textarea").forEach((el) => {
    if (!el.name || el.disabled) return;
    if (el.type === "checkbox") data[el.name] = el.checked ? "1" : "";
    else if (el.type === "radio") { if (el.checked) data[el.name] = el.value; }
    else data[el.name] = el.value;
  });
  return data;
}

function saveDraft(form) {
  const key = formKey(form);
  if (!key) return;
  try {
    localStorage.setItem(storageKey(key), JSON.stringify(serializeForm(form)));
    updateBanner();
  } catch { /* private mode / quota — autosave is best-effort */ }
}

export function clearDraftFor(form) {
  const key = formKey(form);
  if (!key) return;
  try { localStorage.removeItem(storageKey(key)); } catch { /* ignore */ }
}

function snapshotAllForms() {
  document.querySelectorAll("form").forEach((form) => saveDraft(form));
}

function restoreDrafts() {
  document.querySelectorAll("form").forEach((form) => {
    const key = formKey(form);
    if (!key) return;
    let raw = null;
    try { raw = localStorage.getItem(storageKey(key)); } catch { return; }
    if (!raw) return;
    let data;
    try { data = JSON.parse(raw); } catch { localStorage.removeItem(storageKey(key)); return; }
    let applied = false;
    Object.entries(data).forEach(([name, value]) => {
      const els = form.querySelectorAll(`[name="${CSS.escape(name)}"]`);
      els.forEach((el) => {
        if (el.type === "checkbox") { el.checked = value === "1"; applied = true; }
        else if (el.type === "radio") { el.checked = el.value === value; applied = true; }
        else if (el.value !== value) { el.value = value; applied = true; }
      });
    });
    if (applied) {
      form.classList.add("has-restored-draft");
      // Let dependent UI (computed fields, validation hints) react to the
      // restored values exactly as it would to manual typing.
      form.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });
  updateBanner();
}

function hasDrafts() {
  try {
    return Object.keys(localStorage).some((k) => k.startsWith(DRAFT_PREFIX));
  } catch { return false; }
}

function ensureBanner() {
  if (bannerEl || !hasDrafts()) return;
  bannerEl = document.createElement("div");
  bannerEl.className = "status-box draft-restore-banner";
  bannerEl.innerHTML =
    '<span>Unsaved drafts were restored from your last session.</span> ' +
    '<button type="button" class="link-button">Discard all drafts</button>';
  bannerEl.querySelector("button").addEventListener("click", () => {
    Object.keys(localStorage)
      .filter((k) => k.startsWith(DRAFT_PREFIX))
      .forEach((k) => localStorage.removeItem(k));
    document.querySelectorAll(".draft-restore-banner").forEach((b) => b.remove());
    bannerEl = null;
  });
  const anchor = document.getElementById("runtime-status");
  if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(bannerEl, anchor.nextSibling);
  else document.body.prepend(bannerEl);
}

function updateBanner() {
  if (hasDrafts()) ensureBanner();
  else if (bannerEl) { bannerEl.remove(); bannerEl = null; }
}

export function initAutosave() {
  // Capture every edit in every form (delegation survives dynamically
  // rendered workspaces like clinical/investigation forms).
  document.addEventListener("input", (event) => {
    const form = event.target.closest("form");
    if (!form) return;
    clearTimeout(timer);
    timer = setTimeout(() => saveDraft(form), DEBOUNCE_MS);
  }, true);
  document.addEventListener("change", (event) => {
    const form = event.target.closest("form");
    if (form) saveDraft(form);
  }, true);

  // Successful submits mean the draft is no longer needed.
  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form");
    if (form) clearDraftFor(form);
  }, true);

  // Warn on leaving the page while local drafts (i.e. unsubmitted edits) exist.
  window.addEventListener("beforeunload", (event) => {
    snapshotAllForms(); // flush anything typed within the debounce window
    if (hasDrafts()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  window.addEventListener("pagehide", snapshotAllForms);

  // Server/connection lost → freeze a final snapshot of everything on screen
  // so the last entered step is never lost even if the machine dies next.
  window.addEventListener("hhms:server-state", (event) => {
    if (event.detail && event.detail.online === false) snapshotAllForms();
  });
  window.addEventListener("hhms:request-timeout", snapshotAllForms);
  window.addEventListener("offline", snapshotAllForms);

  restoreDrafts();
}
