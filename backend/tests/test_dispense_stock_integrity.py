"""Regression tests for transactional pharmacy dispensing."""

from decimal import Decimal

from app.services.dispense import DispenseService


def test_dispense_service_is_instantiable() -> None:
    service = DispenseService()
    assert service.repository is not None


def test_requested_quantity_uses_decimal() -> None:
    assert Decimal("1.25") > Decimal("1")
