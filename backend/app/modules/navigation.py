"""
The navigation manifest.

One declaration of what appears in the sidebar, so that the three things that
decide it - which module owns the screen, which permission opens it, and what the
user is looking at - are stated once instead of being spread across hardcoded HTML
and a role map in the client.

The client renders from this. The static markup in ``index.html`` remains as a
fallback for the case where the request fails, and a test asserts the fallback
matches this list exactly, so the two cannot drift.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavGroup:
    """A heading in the sidebar, and where it sits.

    Order is the order a hospital works in, not the alphabet: the front desk opens
    patients before anyone looks at a report, and administration is last because
    nobody opens it twice a day.
    """

    code: str
    label: str
    order: int


#: Six groups over fourteen screens. The flat list was fourteen buttons in a column,
#: which is not a menu - it is a list of everything the software can do, in the order
#: it happened to be built.
NAV_GROUPS: tuple[NavGroup, ...] = (
    NavGroup("front-desk", "Front Desk", 10),
    NavGroup("clinical", "Clinical", 20),
    NavGroup("stock", "Pharmacy & Stock", 30),
    NavGroup("reporting", "Reports & Statistics", 40),
    NavGroup("records", "Records & Audit", 50),
    NavGroup("administration", "Administration", 90),
)

BY_GROUP: dict[str, NavGroup] = {group.code: group for group in NAV_GROUPS}


@dataclass(frozen=True)
class NavItem:
    """One sidebar entry."""

    view: str
    label: str
    module: str
    permission: str | None
    group: str = "clinical"


#: Order is the order a hospital works in: patients first, administration last.
NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("dashboard", "Dashboard", "core", None, "front-desk"),
    NavItem("patients", "Patients", "core", "patients.read", "front-desk"),
    NavItem("opd", "OPD Queue", "core", "opd.read", "front-desk"),
    NavItem("ipd-management", "IPD Management", "ipd", "ipd.read", "clinical"),
    NavItem("inventory", "Inventory", "stock", "inventory.read", "stock"),
    NavItem("procurement", "Procurement", "stock", "procurement.read", "stock"),
    NavItem("statistics", "Statistics", "core", "reporting.read", "reporting"),
    NavItem("reports", "Reports / Printing", "core", "reporting.read", "reporting"),
    NavItem("historical", "Historical Data", "core", "reporting.read", "reporting"),
    NavItem("activity", "Audit / Activity", "core", "audit.read", "records"),
    NavItem("administration", "Administration", "core", "users.read", "administration"),
    NavItem("settings", "Settings", "core", "settings.read", "administration"),
    NavItem("backups", "Backups", "core", "backup.read", "administration"),
    NavItem("system-health", "System Health", "core", "health.read", "administration"),
)


BY_VIEW: dict[str, NavItem] = {item.view: item for item in NAV_ITEMS}

__all__ = ["BY_GROUP", "BY_VIEW", "NAV_GROUPS", "NAV_ITEMS", "NavGroup", "NavItem"]
