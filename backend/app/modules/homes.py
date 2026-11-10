"""
What each role sees when it logs in.

A receptionist and a medical superintendent opened the same dashboard, which meant
the receptionist scrolled past ward occupancy to reach the patient list, and the
superintendent saw a queue they never work in.

A home is a short, ordered set of panels. It is not a permission - the permissions
decide what a role *may* open; this decides what it *should* open first. A role with
no declared home falls back to the default rather than to a blank screen, because a
blank screen reads as a broken system.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HomePanel:
    """One block on a home screen."""

    kind: str
    title: str
    #: The view this panel opens, when the panel is a shortcut.
    view: str | None = None
    #: The dashboard endpoint that feeds it, when the panel shows numbers.
    source: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Home:
    """A role's landing screen."""

    key: str
    title: str
    subtitle: str
    panels: tuple[HomePanel, ...] = field(default_factory=tuple)


#: The default: what somebody sees whose role has no declared home.
DEFAULT_HOME = Home(
    key="default",
    title="Home",
    subtitle="Your screens are in the menu on the left.",
    panels=(
        HomePanel("shortcut", "Patients", view="patients", description="Find a patient record."),
        HomePanel("shortcut", "OPD Queue", view="opd", description="Today's queue."),
    ),
)

HOMES: dict[str, Home] = {
    "registration desk": Home(
        key="front-desk",
        title="Front Desk",
        subtitle="Register patients and keep the queue moving.",
        panels=(
            HomePanel("shortcut", "Register a patient", view="patients"),
            HomePanel("shortcut", "OPD Queue", view="opd", description="Who is waiting right now."),
        ),
    ),
    "medical officer": Home(
        key="clinician",
        title="Your Clinic",
        subtitle="Today's patients and their records.",
        panels=(
            HomePanel("shortcut", "OPD Queue", view="opd"),
            HomePanel("shortcut", "Patients", view="patients"),
            HomePanel("shortcut", "IPD Management", view="ipd-management"),
        ),
    ),
    "medical superintendent": Home(
        key="superintendent",
        title="Hospital Overview",
        subtitle="Everything the hospital is doing, at a glance.",
        panels=(
            HomePanel("metrics", "Statistics", view="statistics", source="/statistics/summary"),
            HomePanel("shortcut", "IPD Management", view="ipd-management"),
            HomePanel("shortcut", "Audit / Activity", view="activity"),
        ),
    ),
    "pharmacist": Home(
        key="pharmacy",
        title="Pharmacy",
        subtitle="Dispensing and stock.",
        panels=(
            HomePanel("shortcut", "Inventory", view="inventory"),
            HomePanel("shortcut", "Procurement", view="procurement"),
        ),
    ),
    "billing staff": Home(
        key="billing",
        title="Billing",
        subtitle="Invoices and receipts.",
        panels=(
            HomePanel("shortcut", "Reports / Printing", view="reports"),
            HomePanel("shortcut", "Patients", view="patients"),
        ),
    ),
    "medical records": Home(
        key="records",
        title="Medical Records",
        subtitle="Files, archives and certificates.",
        panels=(
            HomePanel("shortcut", "Patients", view="patients"),
            HomePanel("shortcut", "Historical Data", view="historical"),
        ),
    ),
    "store keeper": Home(
        key="store",
        title="Stores",
        subtitle="Stock and purchasing.",
        panels=(
            HomePanel("shortcut", "Inventory", view="inventory"),
            HomePanel("shortcut", "Procurement", view="procurement"),
        ),
    ),
    "laboratory staff": Home(
        key="laboratory",
        title="Laboratory",
        subtitle="Investigations requested and reported.",
        panels=(
            HomePanel("shortcut", "Patients", view="patients"),
        ),
    ),
    "auditor": Home(
        key="auditor",
        title="Audit",
        subtitle="What happened, when, and by whom.",
        panels=(
            HomePanel("shortcut", "Audit / Activity", view="activity"),
            HomePanel("shortcut", "Statistics", view="statistics"),
        ),
    ),
}

#: Order matters: the most senior role decides the home when a user holds several.
#: A medical superintendent who is also on the registration desk should land on the
#: hospital overview, not the queue.
ROLE_PRECEDENCE: tuple[str, ...] = (
    "administrator",
    "medical superintendent",
    "auditor",
    "medical officer",
    "medical records",
    "pharmacist",
    "laboratory staff",
    "billing staff",
    "store keeper",
    "registration desk",
)


def home_for(roles: list[str] | tuple[str, ...]) -> Home:
    """The home for a set of role names, by precedence, with a default."""

    held = {role.strip().lower() for role in roles if role}
    if "administrator" in held:
        # The administrator's job is the whole hospital, so it gets the overview.
        return HOMES["medical superintendent"]

    for role in ROLE_PRECEDENCE:
        if role in held and role in HOMES:
            return HOMES[role]
    return DEFAULT_HOME


__all__ = ["DEFAULT_HOME", "HOMES", "ROLE_PRECEDENCE", "Home", "HomePanel", "home_for"]
