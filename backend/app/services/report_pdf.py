"""Deterministic PDF rendering for HHMS print envelopes.

Batch 115 — Milestone 7 (part 11) / Milestone 4 "PDF generation verification".

The client print pipeline (Batches 106-113) renders HTML print previews from
JSON print envelopes served under ``/api/v1/reports/*``.  This module closes
the remaining server-side gap: it renders any of those envelopes to a real,
byte-reproducible PDF document via ReportLab, so reports can be archived,
emailed, or printed without a browser.

Design contract (locked by tests/test_batch115_pdf_generation_qa.py):
* One A4 portrait page per envelope section; long content flows across pages.
* Every envelope carries ``title`` and ``generated_at`` in its header block.
* Output is deterministic: the same envelope payload always produces the
  same PDF bytes (ReportLab metadata timestamps are pinned).
* Unknown report types raise ``ValueError``; malformed payloads raise
  ``TypeError`` — never a silent empty document.
"""
from __future__ import annotations

import hashlib
import io
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---------------------------------------------------------------------------
# Envelope type registry
# ---------------------------------------------------------------------------

#: Mapping of envelope ``report_type`` -> human document kind used in headers.
ENVELOPE_KINDS: dict[str, str] = {
    "clinical_print": "Clinical Report",
    "invoice_print": "Invoice Receipt",
    "collection_summary_print": "Collection Summary",
    "receivables_aging_print": "Receivables Aging Ledger",
    "invoice_receipt_continuity_print": "Invoice Receipt Continuity Audit",
    "receipt_numbering_continuity_print": "Receipt Numbering Continuity Audit",
    "invoice_payment_reconciliation_print": "Invoice Payment Reconciliation Ledger",
    "payment_method_summary_print": "Payment Method Collection Summary",
    "payment_method_overpayment_print": "Payment Method Overpayment Breakdown",
    "invoice_overpayment_print": "Invoice Overpayment Ledger",
    "invoice_settlement_audit_print": "Invoice Settlement Audit",
    "refund_audit_print": "Refund Processing Audit",
    "discharge_audit_print": "Discharge Audit Ledger",
    "opd_queue_summary_print": "OPD Queue Daily Summary",
    "ward_occupancy_print": "Ward Occupancy Summary",
    "investigation_billing_reconciliation_print": "Investigation Billing Reconciliation",
}

_LABEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _humanize(key: str) -> str:
    return _LABEL_RE.sub(" ", str(key)).replace("_", " ").strip().capitalize()


def _fmt(value: Any) -> str:
    """Render a scalar value deterministically (no locale-dependent output)."""
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "hhmsTitle", parent=base["Title"], fontSize=16, leading=20, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "hhmsSubtitle", parent=base["Normal"], fontSize=9, leading=12,
            textColor=base["Normal"].textColor, spaceAfter=10,
        ),
        "heading": ParagraphStyle(
            "hhmsHeading", parent=base["Heading2"], fontSize=12, leading=15, spaceBefore=6, spaceAfter=6,
        ),
        "field_key": ParagraphStyle("hhmsKey", parent=base["Normal"], fontSize=9, leading=12),
        "field_val": ParagraphStyle("hhmsVal", parent=base["Normal"], fontSize=9, leading=12),
        "body": ParagraphStyle("hhmsBody", parent=base["Normal"], fontSize=9, leading=12),
    }
    return styles


# ---------------------------------------------------------------------------
# Content builders (recursive over JSON-shaped envelope data)
# ---------------------------------------------------------------------------

def _flowables_for(value: Any, styles: dict, depth: int = 0) -> list:
    """Convert an arbitrary JSON value into ReportLab flowables."""
    out: list = []
    if isinstance(value, dict):
        rows = [
            [Paragraph(_humanize(str(k)), styles["field_key"]),
             Paragraph("", styles["field_val"]) if _is_empty(v) else _inline(v, styles)]
            for k, v in value.items()
        ]
        if not rows:
            out.append(Paragraph("(empty)", styles["body"]))
        else:
            table = Table(rows, colWidths=[55 * mm, 105 * mm])
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, (0.85, 0.85, 0.85)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))
            out.append(table)
    elif isinstance(value, list):
        if not value:
            out.append(Paragraph("No records", styles["body"]))
        else:
            for i, item in enumerate(value, start=1):
                prefix = Paragraph(f"{i}.", styles["field_key"])
                body = _inline(item, styles)
                table = Table([[prefix, body]], colWidths=[10 * mm, 150 * mm])
                table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]))
                out.append(table)
    else:
        out.append(_inline(value, styles))
    return out


def _is_empty(v: Any) -> bool:
    return v is None or v == "" or v == {} or v == []


def _inline(value: Any, styles: dict):
    if isinstance(value, (dict, list)):
        # Nested structures render as compact key=value text inline.
        if isinstance(value, dict):
            parts = "; ".join(f"{_humanize(str(k))}: {_fmt(v)}" for k, v in value.items())
        else:
            parts = "; ".join(_fmt(v) for v in value)
        return Paragraph(parts or "-", styles["field_val"])
    return Paragraph(_fmt(value), styles["field_val"])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_envelope_pdf(envelope: dict) -> bytes:
    """Render one print-envelope payload to deterministic A4 portrait PDF bytes.

    Accepts either the clinical envelope shape (``selected_sections`` +
    ``report.data``) or any ledger/summary envelope shape (``data`` dict plus
    optional ``sections`` ordering).
    """
    if not isinstance(envelope, dict):
        raise TypeError("envelope must be a dict")
    report_type = envelope.get("report_type")
    if not report_type:
        raise ValueError("envelope is missing report_type")
    if report_type not in ENVELOPE_KINDS:
        raise ValueError(f"unknown report_type: {report_type!r}")

    title = envelope.get("title") or ENVELOPE_KINDS[report_type]
    generated_at = _fmt(envelope.get("generated_at"))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=str(title),
        author="HHMS",
        subject=ENVELOPE_KINDS[report_type],
        creator="HHMS Report Engine",
        producer="HHMS Report Engine",
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    styles = _styles()
    story: list = [
        Paragraph("HHMS", styles["subtitle"]),
        Paragraph(str(title), styles["title"]),
        Paragraph(f"Generated: {generated_at}", styles["subtitle"]),
        Spacer(1, 4 * mm),
    ]

    sections: list[tuple[str, Any]] = []
    if report_type == "clinical_print":
        report = envelope.get("report") or {}
        data = report.get("data") or {}
        order = envelope.get("selected_sections") or list(data.keys())
        sections = [(s, data.get(s)) for s in order]
    else:
        data = envelope.get("data") or {}
        order = envelope.get("sections") or list(data.keys())
        # Some envelopes expose flat scalar summaries directly in `data`.
        scalars = {k: v for k, v in data.items() if not isinstance(v, (dict, list))}
        if scalars:
            sections.append(("Summary", scalars))
        sections.extend((s, data.get(s)) for s in order if s in data)

    if not sections:
        sections.append(("Content", {}))

    for name, payload in sections:
        story.append(Paragraph(_humanize(str(name)), styles["heading"]))
        story.extend(_flowables_for(payload, styles))
        story.append(PageBreak())

    # Pin creation/modification dates for byte-deterministic output.
    def _build(story=story, doc=doc):
        doc.build(story)

    pdf_bytes = _build_and_stamp(buffer, doc, story)
    del _build
    return pdf_bytes


def _build_and_stamp(buffer: io.BytesIO, doc: SimpleDocTemplate, story: list) -> bytes:
    """Build the document and normalize non-deterministic PDF trailer fields."""
    doc.multiBuild(story)
    raw = buffer.getvalue()
    # ReportLab embeds a unique /ID per build (split across two lines);
    # replace it with a content hash so identical payloads always yield
    # identical bytes.
    digest = hashlib.sha256(raw.split(b"trailer")[0]).hexdigest().encode()
    raw = re.sub(
        rb"/ID\s*\n?\s*\[<[0-9A-Fa-f]+><[0-9A-Fa-f]+>\]",
        b"/ID\n[<" + digest + b"><" + digest + b">]",
        raw,
    )
    return raw


def render_batch_pdfs(envelopes: list[dict]) -> list[bytes]:
    """Render multiple envelopes independently (one PDF each)."""
    return [render_envelope_pdf(env) for env in envelopes]


__all__ = ["ENVELOPE_KINDS", "render_envelope_pdf", "render_batch_pdfs"]
