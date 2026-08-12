"""
HHMS Billing API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceRead,
    InvoiceSummary,
    InvoiceUpdate,
    PaymentCreate,
    PaymentRead,
)
from app.services.billing import billing_service


router = APIRouter(
    prefix="/billing",
    tags=["Billing"],
)


@router.get(
    "/invoices",
    response_model=list[InvoiceRead],
)
async def list_invoices(
    db: DatabaseSession,
    _: CurrentUserDependency,
    patient_id: int | None = Query(
        default=None,
        gt=0,
    ),
    payment_status: str | None = Query(
        default=None,
        max_length=20,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[InvoiceRead]:
    return await billing_service.list_invoices(
        db,
        patient_id=patient_id,
        payment_status=payment_status,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/invoices",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(
    invoice_in: InvoiceCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> InvoiceRead:
    subject = current_user.get("sub")

    try:
        generated_by = int(subject)
    except (TypeError, ValueError) as exc:
        from app.core.exceptions import (
            AuthenticationException,
        )

        raise AuthenticationException(
            "Authenticated user identity is invalid."
        ) from exc

    return await billing_service.create_invoice(
        db,
        invoice_in,
        generated_by,
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceRead,
)
async def get_invoice(
    invoice_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvoiceRead:
    return await billing_service.get_invoice(
        db,
        invoice_id,
    )


@router.patch(
    "/invoices/{invoice_id}",
    response_model=InvoiceRead,
)
async def update_invoice(
    invoice_id: int,
    invoice_in: InvoiceUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvoiceRead:
    return await billing_service.update_invoice(
        db,
        invoice_id=invoice_id,
        data=invoice_in,
    )


@router.get(
    "/invoices/{invoice_id}/summary",
    response_model=InvoiceSummary,
)
async def get_invoice_summary(
    invoice_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> InvoiceSummary:
    (
        invoice,
        total_paid,
        balance,
    ) = await billing_service.invoice_summary(
        db,
        invoice_id,
    )

    return InvoiceSummary(
        invoice=invoice,
        total_paid=total_paid,
        balance_amount=balance,
    )


@router.get(
    "/invoices/{invoice_id}/payments",
    response_model=list[PaymentRead],
)
async def list_invoice_payments(
    invoice_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[PaymentRead]:
    return await billing_service.list_payments(
        db,
        invoice_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/payments",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payment_in: PaymentCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> PaymentRead:
    subject = current_user.get("sub")

    try:
        received_by = int(subject)
    except (TypeError, ValueError) as exc:
        from app.core.exceptions import (
            AuthenticationException,
        )

        raise AuthenticationException(
            "Authenticated user identity is invalid."
        ) from exc

    return await billing_service.create_payment(
        db,
        payment_in,
        received_by,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentRead,
)
async def get_payment(
    payment_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PaymentRead:
    return await billing_service.get_payment(
        db,
        payment_id,
    )


__all__ = [
    "router",
]