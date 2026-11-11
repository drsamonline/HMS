"""
Editions.

The product ships in tiers, and a tier is a set of modules plus the licence that
governs it. Declaring them here means the tier is enforced by the same registry that
already gates mounting and navigation, rather than by a separate mechanism that could
disagree with it.

Two decisions are recorded in the shape of this file rather than in a document:

* The free edition is **free to use, not free to copy**. Its licence permits personal
  use and forbids redistribution, which is what makes a free tier compatible with a
  proprietary codebase.
* A tier is **enforced on the server**. Modules outside the edition cannot be enabled
  by the wizard, by the configuration API or by a crafted request - not because a
  customer would cheat, but because a tier that is only a licence paragraph is not a
  tier, it is a hope.

What this does not do: it does not remove code from the build. A disabled module is
present and switched off. Build-time stripping is a packaging step for a later batch,
and until it exists the honest position is that the free edition is a licensed
restriction, not a technical impossibility.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edition:
    """A tier of the product."""

    code: str
    name: str
    #: The licence that governs it, as it should be named on a quotation.
    licence: str
    #: One line a salesperson can repeat without checking.
    summary: str
    #: Module codes this edition may enable. ``core`` is always included.
    modules: tuple[str, ...]
    #: Capabilities that are not modules - a print bundle, for instance.
    features: tuple[str, ...] = ()


#: The free tier: a single-doctor OPD practice. Registration, consultation,
#: dispensing, billing, and the ability to print a whole case and its bills. No
#: inpatient, no laboratory, no compliance reporting - because a personal practice
#: has no NABH assessment to prepare for.
PERSONAL = Edition(
    code="personal",
    name="HHMS Personal",
    licence="PolyForm Noncommercial 1.0.0",
    summary="Free for personal use. One clinic, OPD only, prints the full case and bills.",
    # NABH accredits small healthcare organisations as well as hospitals, so the
    # module is available even here. It is off until somebody turns it on.
    modules=("core", "pharmacy", "billing", "nabh"),
    features=("print_case_bundle", "print_bills"),
)

CLINIC = Edition(
    code="clinic",
    name="HHMS Clinic",
    licence="Commercial licence",
    summary="Multi-doctor clinic: OPD, pharmacy, stock and billing, with laboratory.",
    modules=("core", "pharmacy", "billing", "stock", "laboratory", "nabh"),
    features=("print_case_bundle", "print_bills"),
)

HOSPITAL = Edition(
    code="hospital",
    name="HHMS Hospital",
    licence="Commercial licence",
    summary="Full inpatient hospital, with NABH compliance available but optional.",
    modules=("core", "pharmacy", "billing", "stock", "laboratory", "ipd", "mrd", "nabh"),
    features=("print_case_bundle", "print_bills", "print_discharge"),
)

ENTERPRISE = Edition(
    code="enterprise",
    name="HHMS Enterprise",
    licence="Commercial licence",
    summary="Everything, including NABH and NCH compliance reporting and indicators.",
    modules=("core", "pharmacy", "billing", "stock", "laboratory", "ipd", "mrd", "nabh"),
    features=(
        "print_case_bundle",
        "print_bills",
        "print_discharge",
        "compliance_returns",
        # QCI applies to colleges and teaching hospitals with attached facilities,
        # which is what this edition is for.
        "qci_accreditation",
    ),
)

EDITIONS: dict[str, Edition] = {
    edition.code: edition for edition in (PERSONAL, CLINIC, HOSPITAL, ENTERPRISE)
}

#: The edition an installation runs when nothing says otherwise. The free one, so a
#: hospital that has paid for more must say so rather than getting it by omission.
DEFAULT_EDITION = PERSONAL.code


def edition_for(code: str | None) -> Edition:
    """The edition by code, falling back to the default rather than failing.

    A mistyped environment variable should give a working installation with fewer
    features, not a server that will not start.
    """

    return EDITIONS.get((code or DEFAULT_EDITION).strip().lower(), EDITIONS[DEFAULT_EDITION])


def current_edition() -> Edition:
    """The edition this installation runs, read from the environment once.

    A build-time fact like the port and the discovery name: it is read before the
    database is open, so it cannot be a setting (D-032).
    """

    import os

    return edition_for(os.environ.get("HHMS_EDITION"))


def allows_module(edition: Edition, module_code: str) -> bool:
    return module_code in edition.modules


def allows_feature(edition: Edition, feature: str) -> bool:
    return feature in edition.features


__all__ = [
    "CLINIC",
    "DEFAULT_EDITION",
    "DEFAULT_EDITION",
    "EDITIONS",
    "ENTERPRISE",
    "HOSPITAL",
    "PERSONAL",
    "Edition",
    "allows_feature",
    "allows_module",
    "current_edition",
    "edition_for",
]
