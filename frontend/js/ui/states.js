/* The three states every screen has and most screens forget.
 *
 * A list that is empty because there is nothing yet, a list that is empty because
 * the search matched nothing, and a list that failed to load look identical when
 * all three render "No data." The difference matters to whoever is standing at the
 * desk wondering whether the system is broken.
 */

import { escapeHtml } from "./dialog.js";

/** Nothing exists yet, and here is what to do about it. */
export function emptyState({ title, message, actionLabel, actionId }) {
  return `
    <div class="ui-state ui-state-empty">
      <p class="ui-state-title">${escapeHtml(title || "Nothing here yet")}</p>
      ${message ? `<p class="ui-state-message">${escapeHtml(message)}</p>` : ""}
      ${actionLabel && actionId ? `<button id="${escapeHtml(actionId)}">${escapeHtml(actionLabel)}</button>` : ""}
    </div>`;
}

/** The search worked; nothing matched it. */
export function noResultsState({ query } = {}) {
  return `
    <div class="ui-state ui-state-empty">
      <p class="ui-state-title">No matches</p>
      <p class="ui-state-message">${
        query ? `Nothing matched "${escapeHtml(query)}".` : "Nothing matched those filters."
      } Try a different search.</p>
    </div>`;
}

/** Something is loading. Says so, rather than showing an empty table. */
export function loadingState({ label } = {}) {
  return `
    <div class="ui-state ui-state-loading" role="status" aria-live="polite">
      <span class="ui-spinner" aria-hidden="true"></span>
      <span>${escapeHtml(label || "Loading…")}</span>
    </div>`;
}

/**
 * Something failed, and the message is the error rather than "Something went wrong".
 *
 * A hospital cannot act on "an error occurred". It can act on "the server refused
 * the connection", which is why the real message is shown.
 */
export function errorState({ message, retryId } = {}) {
  return `
    <div class="ui-state ui-state-error" role="alert">
      <p class="ui-state-title">Could not load this</p>
      <p class="ui-state-message">${escapeHtml(message || "The server did not answer.")}</p>
      ${retryId ? `<button id="${escapeHtml(retryId)}" class="secondary">Try again</button>` : ""}
    </div>`;
}

/** Wrap an async load so every screen gets the same three states for free. */
export async function withStates(host, load, { retryId } = {}) {
  host.innerHTML = loadingState();
  try {
    return await load();
  } catch (error) {
    host.innerHTML = errorState({ message: error.message, retryId });
    if (retryId) {
      const button = host.querySelector(`#${retryId}`);
      if (button) button.addEventListener("click", () => withStates(host, load, { retryId }));
    }
    return null;
  }
}
