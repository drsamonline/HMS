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

  groupNavigation(visible);

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

/**
 * Put the visible buttons under headings, in the order the server sent.
 *
 * The buttons are moved rather than rebuilt, because their click handlers were
 * bound in app.js before this ran. A heading with nothing under it is removed
 * entirely: a menu that shows "Pharmacy & Stock" to a hospital with no pharmacy is
 * telling that user about a screen they will never open.
 */
function groupNavigation(visible) {
  const nav = document.querySelector(".record-nav");
  if (!nav) return;

  const byView = new Map(visible.map((item) => [item.view, item]));
  const groups = new Map();

  visible.forEach((item) => {
    if (!groups.has(item.group)) {
      groups.set(item.group, {
        label: item.group_label,
        order: item.group_order,
        views: [],
      });
    }
    groups.get(item.group).views.push(item.view);
  });

  // Remove any headings from a previous run, so a re-render does not nest them.
  nav.querySelectorAll(".nav-group").forEach((group) => group.remove());

  const ordered = [...groups.entries()].sort((a, b) => a[1].order - b[1].order);

  ordered.forEach(([code, group]) => {
    const section = document.createElement("section");
    section.className = "nav-group";
    section.dataset.navGroup = code;

    const heading = document.createElement("h2");
    heading.className = "nav-group-title";
    heading.textContent = group.label;
    section.appendChild(heading);

    let moved = 0;
    group.views.forEach((view) => {
      const button = nav.querySelector(`.nav-item[data-app-view="${view}"]`);
      if (button && !button.classList.contains("hidden") && byView.has(view)) {
        section.appendChild(button);
        moved += 1;
      }
    });

    if (moved > 0) nav.appendChild(section);
  });
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

export { NAV_ITEMS, groupNavigation };
