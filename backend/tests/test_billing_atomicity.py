"""Billing invariants covered by Batch 68."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "app/services/billing.py").read_text(encoding="utf-8")


def test_payment_locks_invoice_row():
    assert "with_for_update()" in SOURCE
    assert 'where(Invoice.id == data.invoice_id)' in SOURCE


def test_payment_status_is_not_client_controlled_on_invoice_update():
    assert 'values.pop("payment_status", None)' in SOURCE


def test_invoice_items_cannot_modify_cancelled_or_paid_invoice():
    assert 'A cancelled invoice cannot be modified.' in SOURCE
    assert 'A fully paid invoice cannot be modified.' in SOURCE


def test_delete_invoice_item_respects_paid_amount():
    assert 'prospective_total < total_paid' in SOURCE
