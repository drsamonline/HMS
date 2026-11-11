"""
The guided first run.

A new installation is a set of empty screens. The person who installed it knows what
they are doing; the receptionist who starts on Monday does not, and will not read a
manual before their first patient.

So the software teaches the five things that make up a working day - register a
patient, record a visit, write a prescription, raise a bill, print the case - on data
that belongs to nobody.

Two rules shape it:

* **The tutorial never touches a real patient.** It works on a patient it created and
  marked, and the checks below look only at whether the *steps have been done*, not at
  which patient. A tutorial that asked somebody to practise on a live record would be
  a tutorial that damages the record.
* **Progress is read from the database, not tracked in the browser.** A step is done
  when the hospital has done it. Closing the laptop does not reset the tutorial, and
  the same person can continue on another machine.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialStep:
    """One step of the first run."""

    code: str
    title: str
    #: What to do, in one sentence.
    what: str
    #: Why it matters - the reason somebody would bother.
    why: str
    #: The screen it happens on.
    view: str
    #: The name of the check in app.services.tutorial.CHECKS.
    check: str


STEPS: tuple[TutorialStep, ...] = (
    TutorialStep(
        code="register",
        title="Register a patient",
        what="Open Patients and register somebody called Tutorial Patient.",
        why="Every record in the hospital hangs off a patient. This is the first thing "
        "anybody does, and the one where a misspelling costs the most.",
        view="patients",
        check="has_patient",
    ),
    TutorialStep(
        code="visit",
        title="Start a visit",
        what="Open the OPD queue and start a consultation for that patient.",
        why="A patient is forever; a visit is one day. The queue is how the hospital "
        "knows who is waiting, and a visit is what takes them out of it.",
        view="opd",
        check="has_visit",
    ),
    TutorialStep(
        code="prescribe",
        title="Write a prescription",
        what="Add one medicine to the visit and save it.",
        why="The prescription is the document the patient leaves with. It carries your "
        "name and your registration number, which is why the software will not print it "
        "without them.",
        view="reports",
        check="has_prescription",
    ),
    TutorialStep(
        code="bill",
        title="Raise a bill",
        what="Open Billing and raise one invoice for the visit.",
        why="Money is where a small error becomes an argument. An invoice is traceable "
        "to something that happened, and that is the whole point of it.",
        view="reports",
        check="has_invoice",
    ),
    TutorialStep(
        code="print",
        title="Print the case",
        what="Print the prescription and read it before you hand it over.",
        why="The preview is the document. What you check on screen is what comes out, "
        "and it is the last chance to notice that the registration number is missing.",
        view="reports",
        check="has_print",
    ),
)

BY_CODE: dict[str, TutorialStep] = {step.code: step for step in STEPS}

__all__ = ["BY_CODE", "STEPS", "TutorialStep"]
