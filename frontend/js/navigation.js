/* HHMS navigation.
 *
 * The sidebar used to be fourteen hardcoded buttons filtered by a role map in
 * rbac.js. That map shipped the name of every screen to every browser, and it
 * drifted from the server the moment a module was added.
 *
 * The server now owns the answer: `GET /api/v1/navigation` returns the menu this
 * user should see, already filtered by the modules this hospital has enabled and
 * the permissions this account holds.
 *
 * This module applies that answer to the markup that is already there rather than
 * rebuilding it. Two reasons: the click handlers are bound in app.js before this
 * runs, and a hospital whose navigation request fails must still get a usable
 * sidebar. The static list is therefore the fallback, and a backend test asserts
 * it matches the manifest exactly - so the two cannot drift apart silently.
 */

const NAV_ITEMS = ".nav-item[data-app-view]";

export async function renderNavigation() {
  let visible;
  try {
    const response = await fetch("/api/v1/navigation", {
      credentials: "same-origin",
      headers: authorisationHeader(),
    });
    if (!response.ok) return; // keep the fallback markup as it is
    visible = await response.json();
  } catch {
    return; // offline, or the server went away: the fallback is what a ward needs
  }

  if (!Array.isArray(visible)) return;

  const allowed = new Set(visible.map((item) => item.view));
  let shown = 0;

  document.querySelectorAll(NAV_ITEMS).forEach((button) => {
    const view = button.dataset.appView;
    const keep = allowed.has(view);
    button.classList.toggle("hidden", !keep);
    button.disabled = !keep;
    button.setAttribute("aria-hidden", String(!keep));
    if (keep) shown += 1;
  });

  const notice = document.querySelector("#access-notice");
  if (notice) {
    const none = shown === 0;
    notice.classList.toggle("hidden", !none);
    notice.textContent = none
      ? "No screens are available for your account. Ask an administrator to give your role access."
      : "";
  }

  // Keep the landing view on something the user can actually open.
  const active = document.querySelector(".nav-item.active");
  if (active && active.classList.contains("hidden")) {
    active.classList.remove("active");
    document.querySelector(`${NAV_ITEMS}:not(.hidden):not([disabled])`)?.classList.add("active");
  }
}

function authorisationHeader() {
  try {
    const token =
      localStorage.getItem("hhms_token") || localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export { NAV_ITEMS };
