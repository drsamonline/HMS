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
class NavItem:
    """One sidebar entry."""

    view: str
    label: str
    module: str
    permission: str | None
    group: str = "clinical"


#: Order is the order a hospital works in: patients first, administration last.
NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("dashboard", "Dashboard", "core", None),
    NavItem("patients", "Patients", "core", "patients.read"),
    NavItem("opd", "OPD Queue", "core", "opd.read"),
    NavItem("ipd-management", "IPD Management", "ipd", "ipd.read"),
    NavItem("statistics", "Statistics", "core", "reporting.read"),
    NavItem("reports", "Reports / Printing", "core", "reporting.read"),
    NavItem("inventory", "Inventory", "stock", "inventory.read"),
    NavItem("procurement", "Procurement", "stock", "procurement.read"),
    NavItem("activity", "Audit / Activity", "core", "audit.read"),
    NavItem("administration", "Administration", "core", "users.read"),
    NavItem("settings", "Settings", "core", "settings.read"),
    NavItem("backups", "Backups", "core", "backup.read"),
    NavItem("system-health", "System Health", "core", "health.read"),
    NavItem("historical", "Historical Data", "core", "reporting.read"),
)


BY_VIEW: dict[str, NavItem] = {item.view: item for item in NAV_ITEMS}

__all__ = ["BY_VIEW", "NAV_ITEMS", "NavItem"]
