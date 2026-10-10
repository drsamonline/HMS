"""HHMS annual archive management and historical case access."""
from __future__ import annotations

import asyncio
import hashlib
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.runtime_paths import archive_directory, cold_archive_directory, database_path
from app.config.settings import get_settings
from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.models.archive_manifest import ArchiveManifest
from app.models.admission import Admission
from app.models.admission_archive_reference import AdmissionArchiveReference
from app.models.billing_archive_reference import (
    InvoiceArchiveReference,
    PaymentArchiveReference,
)
from app.models.case_archive_reference import CaseArchiveReference
from app.models.case_record import CaseRecord
from app.models.clinical_archive_reference import (
    PrescriptionArchiveReference,
    PrescriptionItemArchiveReference,
)
from app.models.diagnosis import Diagnosis
from app.models.dispense_record import DispenseRecord
from app.models.followup import FollowUp
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.investigation import Investigation
from app.models.investigation_result import InvestigationResult
from app.models.lab_archive_reference import InvestigationArchiveReference
from app.models.medical_document import MedicalDocument
from app.models.mrd_archive_reference import MedicalDocumentArchiveReference
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.procurement_archive_reference import (
    GoodsReceiptArchiveReference,
    PurchaseOrderArchiveReference,
    StockCardArchiveReference,
    StockTransactionArchiveReference,
)
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.stock_batch import StockBatch
from app.models.stock_card import StockCard
from app.models.stock_transaction import StockTransaction
from app.models.payment import Payment
from app.models.pharmacy_archive_reference import DispenseArchiveReference
from app.models.visit import Visit
from app.models.visit_archive_reference import VisitArchiveReference
from app.services.operational_year import operational_year_service


def _copy_sqlite(source: Path, target: Path) -> None:
    src = sqlite3.connect(source)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
        dst.commit()
    finally:
        dst.close()
        src.close()


def _integrity(path: Path) -> bool:
    con = sqlite3.connect(path)
    try:
        result = con.execute("PRAGMA integrity_check").fetchone()
        return bool(result and result[0] == "ok")
    finally:
        con.close()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ArchiveManager:
    """Create verified annual snapshots and perform safe case rollover."""

    async def _prepare_archive_file(
        self,
        db: AsyncSession,
        year: int,
        tier: str | None = None,
    ) -> tuple[Path, str, int]:
        source = database_path()
        if not source.exists():
            raise ResourceNotFoundException("HHMS database does not exist.")

        op_cfg = await operational_year_service.get_config(db)
        current_year = operational_year_service.current_year(date.today(), op_cfg)
        if year >= current_year:
            raise BusinessRuleException("Only completed operational years can be archived.")

        age = current_year - year
        settings = get_settings()
        if age > settings.COLD_ARCHIVE_YEARS:
            raise BusinessRuleException(
                "Requested archive is outside the configured retention window."
            )

        chosen = tier or (
            "online" if age <= settings.ONLINE_ARCHIVE_YEARS else "cold"
        )
        if chosen not in {"online", "cold"}:
            raise BusinessRuleException("Archive storage tier must be online or cold.")
        if chosen == "online" and age > settings.ONLINE_ARCHIVE_YEARS:
            raise BusinessRuleException("Archive age exceeds the online archive window.")

        base = cold_archive_directory() if chosen == "cold" else archive_directory()
        outdir = base / str(year)
        outdir.mkdir(parents=True, exist_ok=True)
        target = outdir / (
            f"HHMS_{year}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}.sqlite3"
        )
        await asyncio.to_thread(_copy_sqlite, source, target)
        if not await asyncio.to_thread(_integrity, target):
            target.unlink(missing_ok=True)
            raise BusinessRuleException("Archive integrity check failed.")
        checksum = await asyncio.to_thread(_sha256, target)
        return target, chosen, checksum

    async def create_year_archive(
        self,
        db: AsyncSession,
        year: int,
        tier: str | None = None,
    ) -> ArchiveManifest:
        existing = await db.scalar(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        if existing and existing.verified:
            return existing

        target, chosen, checksum = await self._prepare_archive_file(db, year, tier)
        try:
            if existing:
                existing.storage_tier = chosen
                existing.file_path = str(target)
                existing.checksum_sha256 = checksum
                existing.size_bytes = target.stat().st_size
                existing.verified = True
                await db.commit()
                await db.refresh(existing)
                return existing

            row = ArchiveManifest(
                archive_year=year,
                storage_tier=chosen,
                file_path=str(target),
                checksum_sha256=checksum,
                size_bytes=target.stat().st_size,
                verified=True,
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return row
        except Exception:
            target.unlink(missing_ok=True)
            raise

    async def rollover_preview(self, db: AsyncSession) -> dict[str, Any]:
        cfg = await operational_year_service.get_config(db)
        current_year = operational_year_service.current_year(date.today(), cfg)
        target_year = current_year - get_settings().LIVE_DATA_YEARS
        existing = await db.scalar(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == target_year)
        )
        result = await db.execute(
            select(CaseRecord.id).where(CaseRecord.case_year == target_year)
        )
        case_count = len(result.scalars().all())
        visit_result = await db.execute(
            select(Visit.id).where(Visit.visit_year == target_year)
        )
        visit_count = len(visit_result.scalars().all())
        invoice_result = await db.execute(
            select(Invoice.id).where(Invoice.invoice_year == target_year)
        )
        invoice_count = len(invoice_result.scalars().all())
        payment_result = await db.execute(
            select(Payment.id).where(Payment.payment_year == target_year)
        )
        payment_count = len(payment_result.scalars().all())
        dispense_result = await db.execute(
            select(DispenseRecord.id).where(DispenseRecord.dispense_year == target_year)
        )
        dispense_count = len(dispense_result.scalars().all())
        investigation_result = await db.execute(
            select(Investigation.id).where(Investigation.investigation_year == target_year)
        )
        investigation_count = len(investigation_result.scalars().all())
        admission_result = await db.execute(
            select(Admission.id).where(Admission.admission_year == target_year)
        )
        admission_count = len(admission_result.scalars().all())
        document_result = await db.execute(
            select(MedicalDocument.id).where(MedicalDocument.document_year == target_year)
        )
        document_count = len(document_result.scalars().all())
        purchase_order_result = await db.execute(
            select(PurchaseOrder.id).where(PurchaseOrder.order_year == target_year)
        )
        purchase_order_count = len(purchase_order_result.scalars().all())
        goods_receipt_result = await db.execute(
            select(GoodsReceipt.id).where(GoodsReceipt.receipt_year == target_year)
        )
        goods_receipt_count = len(goods_receipt_result.scalars().all())
        stock_transaction_result = await db.execute(
            select(StockTransaction.id).where(StockTransaction.transaction_year == target_year)
        )
        stock_transaction_count = len(stock_transaction_result.scalars().all())
        stock_card_result = await db.execute(
            select(StockCard.id).where(StockCard.transaction_year == target_year)
        )
        stock_card_count = len(stock_card_result.scalars().all())
        prescription_result = await db.execute(
            select(Prescription.id).where(Prescription.prescription_year == target_year)
        )
        prescription_count = len(prescription_result.scalars().all())
        prescription_item_result = await db.execute(
            select(PrescriptionItem.id).where(PrescriptionItem.item_year == target_year)
        )
        prescription_item_count = len(prescription_item_result.scalars().all())
        return {
            "current_year": current_year,
            "target_year": target_year,
            "eligible": target_year < current_year,
            "already_archived": bool(existing and existing.verified),
            "case_count": case_count,
            "visit_count": visit_count,
            "invoice_count": invoice_count,
            "payment_count": payment_count,
            "dispense_count": dispense_count,
            "investigation_count": investigation_count,
            "admission_count": admission_count,
            "document_count": document_count,
            "purchase_order_count": purchase_order_count,
            "goods_receipt_count": goods_receipt_count,
            "stock_transaction_count": stock_transaction_count,
            "stock_card_count": stock_card_count,
            "prescription_count": prescription_count,
            "prescription_item_count": prescription_item_count,
        }

    async def rollover_case_year(
        self,
        db: AsyncSession,
        year: int,
    ) -> dict[str, Any]:
        cfg = await operational_year_service.get_config(db)
        current_year = operational_year_service.current_year(date.today(), cfg)
        if year >= current_year:
            raise BusinessRuleException("The current operational year cannot be rolled over.")
        age = current_year - year
        if age < get_settings().LIVE_DATA_YEARS:
            raise BusinessRuleException(
                "The operational year is still inside the live-data retention window."
            )
        existing = await db.scalar(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        if existing:
            raise BusinessRuleException(
                f"Archive rollover for {year} has already been registered."
            )

        backup = None
        target: Path | None = None
        try:
            from app.services.backup import backup_service

            backup = await backup_service.create_backup(f"pre-rollover-{year}")

            cases = list(
                (
                    await db.execute(
                        select(CaseRecord)
                        .where(CaseRecord.case_year == year)
                        .order_by(CaseRecord.id)
                    )
                ).scalars().all()
            )
            visits = list(
                (
                    await db.execute(
                        select(Visit)
                        .where(Visit.visit_year == year)
                        .order_by(Visit.id)
                    )
                ).scalars().all()
            )
            invoices = list(
                (
                    await db.execute(
                        select(Invoice)
                        .where(Invoice.invoice_year == year)
                        .order_by(Invoice.id)
                    )
                ).scalars().all()
            )
            payments = list(
                (
                    await db.execute(
                        select(Payment)
                        .where(Payment.payment_year == year)
                        .order_by(Payment.id)
                    )
                ).scalars().all()
            )
            dispenses = list(
                (
                    await db.execute(
                        select(DispenseRecord)
                        .where(DispenseRecord.dispense_year == year)
                        .order_by(DispenseRecord.id)
                    )
                ).scalars().all()
            )
            investigations = list(
                (
                    await db.execute(
                        select(Investigation)
                        .where(Investigation.investigation_year == year)
                        .order_by(Investigation.id)
                    )
                ).scalars().all()
            )
            admissions = list(
                (
                    await db.execute(
                        select(Admission)
                        .where(Admission.admission_year == year)
                        .order_by(Admission.id)
                    )
                ).scalars().all()
            )
            documents = list(
                (
                    await db.execute(
                        select(MedicalDocument)
                        .where(MedicalDocument.document_year == year)
                        .order_by(MedicalDocument.id)
                    )
                ).scalars().all()
            )
            purchase_orders = list(
                (
                    await db.execute(
                        select(PurchaseOrder)
                        .where(PurchaseOrder.order_year == year)
                        .order_by(PurchaseOrder.id)
                    )
                ).scalars().all()
            )
            goods_receipts = list(
                (
                    await db.execute(
                        select(GoodsReceipt)
                        .where(GoodsReceipt.receipt_year == year)
                        .order_by(GoodsReceipt.id)
                    )
                ).scalars().all()
            )
            stock_transactions = list(
                (
                    await db.execute(
                        select(StockTransaction)
                        .where(StockTransaction.transaction_year == year)
                        .order_by(StockTransaction.id)
                    )
                ).scalars().all()
            )
            stock_cards = list(
                (
                    await db.execute(
                        select(StockCard)
                        .where(StockCard.transaction_year == year)
                        .order_by(StockCard.id)
                    )
                ).scalars().all()
            )
            prescriptions = list(
                (
                    await db.execute(
                        select(Prescription)
                        .where(Prescription.prescription_year == year)
                        .order_by(Prescription.id)
                    )
                ).scalars().all()
            )
            prescription_items = list(
                (
                    await db.execute(
                        select(PrescriptionItem)
                        .where(PrescriptionItem.item_year == year)
                        .order_by(PrescriptionItem.id)
                    )
                ).scalars().all()
            )
            # Items whose parent prescription is being archived roll over with
            # the parent even when their own item_year differs, keeping the
            # Prescription -> PrescriptionItem lineage intact in every year.
            prescription_ids = [prescription.id for prescription in prescriptions]
            if prescription_ids:
                linked_item_rows = list(
                    (
                        await db.execute(
                            select(PrescriptionItem)
                            .where(
                                PrescriptionItem.prescription_id.in_(prescription_ids),
                                PrescriptionItem.id.notin_(
                                    [item.id for item in prescription_items]
                                ),
                            )
                            .order_by(PrescriptionItem.id)
                        )
                    ).scalars().all()
                )
                prescription_items.extend(linked_item_rows)
            target, chosen, checksum = await self._prepare_archive_file(db, year)
            if await db.scalar(
                select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
            ):
                raise BusinessRuleException("Archive registration changed during rollover.")

            manifest = ArchiveManifest(
                archive_year=year,
                storage_tier=chosen,
                file_path=str(target),
                checksum_sha256=checksum,
                size_bytes=target.stat().st_size,
                verified=True,
            )
            db.add(manifest)
            await db.flush()

            for case in cases:
                db.add(
                    CaseArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_case_id=case.id,
                        patient_id=case.patient_id,
                        case_family_id=case.case_family_id,
                        case_number=case.case_number,
                        archive_year=year,
                    )
                )

            for visit in visits:
                db.add(
                    VisitArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_visit_id=visit.id,
                        patient_id=visit.patient_id,
                        visit_number=visit.visit_number,
                        visit_year=year,
                    )
                )

            for invoice in invoices:
                db.add(
                    InvoiceArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_invoice_id=invoice.id,
                        patient_id=invoice.patient_id,
                        invoice_number=invoice.invoice_number,
                        invoice_year=year,
                        total_amount=invoice.total_amount,
                        payment_status=invoice.payment_status,
                    )
                )

            for payment in payments:
                db.add(
                    PaymentArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_payment_id=payment.id,
                        original_invoice_id=payment.invoice_id,
                        receipt_number=payment.receipt_number,
                        payment_year=year,
                        amount_paid=payment.amount_paid,
                        payment_method=payment.payment_method,
                    )
                )

            for dispense in dispenses:
                db.add(
                    DispenseArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_dispense_id=dispense.id,
                        prescription_item_id=dispense.prescription_item_id,
                        dispense_year=year,
                        medicine_id=dispense.medicine_id,
                        quantity_dispensed=dispense.quantity_dispensed,
                        dispense_date=dispense.dispense_date,
                    )
                )

            for investigation in investigations:
                db.add(
                    InvestigationArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_investigation_id=investigation.id,
                        patient_id=investigation.patient_id,
                        visit_id=investigation.visit_id,
                        admission_id=investigation.admission_id,
                        investigation_number=investigation.investigation_number,
                        investigation_year=year,
                    )
                )

            for admission in admissions:
                db.add(
                    AdmissionArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_admission_id=admission.id,
                        patient_id=admission.patient_id,
                        admission_year=year,
                        admission_number=admission.admission_number,
                        admission_datetime=admission.admission_datetime,
                        bed_id=admission.bed_id,
                        department_id=admission.department_id,
                        service_id=admission.service_id,
                        case_type=admission.case_type,
                        admitted_by=admission.admitted_by,
                        admission_status=admission.admission_status,
                    )
                )

            for document in documents:
                db.add(
                    MedicalDocumentArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_document_id=document.id,
                        patient_id=document.patient_id,
                        visit_id=document.visit_id,
                        admission_id=document.admission_id,
                        document_number=document.document_number,
                        document_year=year,
                    )
                )

            for purchase_order in purchase_orders:
                db.add(
                    PurchaseOrderArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_purchase_order_id=purchase_order.id,
                        supplier_id=purchase_order.supplier_id,
                        order_no=purchase_order.order_no,
                        order_year=year,
                    )
                )

            for goods_receipt in goods_receipts:
                db.add(
                    GoodsReceiptArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_goods_receipt_id=goods_receipt.id,
                        goods_receipt_no=goods_receipt.receipt_no,
                        receipt_year=year,
                    )
                )

            for stock_transaction in stock_transactions:
                db.add(
                    StockTransactionArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_stock_transaction_id=stock_transaction.id,
                        inventory_item_id=stock_transaction.inventory_item_id,
                        transaction_type=stock_transaction.transaction_type,
                        reference_number=stock_transaction.reference_number,
                        transaction_year=year,
                    )
                )

            for stock_card in stock_cards:
                db.add(
                    StockCardArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_stock_card_id=stock_card.id,
                        medicine_id=stock_card.medicine_id,
                        transaction_year=year,
                    )
                )

            for prescription in prescriptions:
                db.add(
                    PrescriptionArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_prescription_id=prescription.id,
                        visit_id=prescription.visit_id,
                        prescription_number=prescription.prescription_number,
                        prescription_year=year,
                    )
                )

            for prescription_item in prescription_items:
                db.add(
                    PrescriptionItemArchiveReference(
                        archive_manifest_id=manifest.id,
                        original_item_id=prescription_item.id,
                        original_prescription_id=prescription_item.prescription_id,
                        medicine_id=prescription_item.medicine_id,
                        item_year=year,
                    )
                )

            case_ids = [case.id for case in cases]
            if case_ids:
                now = datetime.now(timezone.utc)
                await db.execute(
                    update(CaseRecord)
                    .where(CaseRecord.renewed_from_case_id.in_(case_ids))
                    .values(renewed_from_case_id=None, updated_at=now)
                )
                await db.execute(
                    update(CaseRecord)
                    .where(CaseRecord.id.in_(case_ids))
                    .values(renewed_from_case_id=None)
                )
                await db.execute(
                    delete(FollowUp).where(FollowUp.case_record_id.in_(case_ids))
                )
                await db.execute(
                    delete(Diagnosis).where(Diagnosis.case_record_id.in_(case_ids))
                )
                await db.execute(delete(CaseRecord).where(CaseRecord.id.in_(case_ids)))

            visit_ids = [visit.id for visit in visits]
            if visit_ids:
                await db.execute(
                    update(CaseRecord)
                    .where(CaseRecord.visit_id.in_(visit_ids))
                    .values(visit_id=None)
                )
                # Batch 77: prescriptions keep their own lifecycle row after the
                # visit is archived; detach the visit pointer so the FK stays
                # consistent (Prescription.visit_id is nullable since 0028).
                await db.execute(
                    update(Prescription)
                    .where(Prescription.visit_id.in_(visit_ids))
                    .values(visit_id=None)
                )
                await db.execute(delete(Visit).where(Visit.id.in_(visit_ids)))

            invoice_ids = [invoice.id for invoice in invoices]
            if invoice_ids:
                # Payment rows for the rolled-over year are removed through their
                # own payment_year rule below; detach any payments that reference
                # invoices being physically archived while remaining live.
                await db.execute(
                    update(Payment)
                    .where(Payment.invoice_id.in_(invoice_ids))
                    .values(invoice_id=None)
                )
                await db.execute(
                    delete(InvoiceItem).where(InvoiceItem.invoice_id.in_(invoice_ids))
                )
                await db.execute(delete(Invoice).where(Invoice.id.in_(invoice_ids)))

            payment_ids = [payment.id for payment in payments]
            if payment_ids:
                await db.execute(
                    delete(Payment).where(Payment.id.in_(payment_ids))
                )

            dispense_ids = [dispense.id for dispense in dispenses]
            if dispense_ids:
                await db.execute(
                    delete(DispenseRecord).where(DispenseRecord.id.in_(dispense_ids))
                )

            investigation_ids = [investigation.id for investigation in investigations]
            if investigation_ids:
                # Results belong to their investigation; archive them with the
                # parent order before removing the investigation rows.
                await db.execute(
                    delete(InvestigationResult).where(
                        InvestigationResult.investigation_id.in_(investigation_ids)
                    )
                )
                await db.execute(
                    delete(Investigation).where(Investigation.id.in_(investigation_ids))
                )

            admission_ids = [admission.id for admission in admissions]
            if admission_ids:
                # Investigations requested during an archived admission keep
                # their patient linkage; detach the episode reference only.
                await db.execute(
                    update(Investigation)
                    .where(Investigation.admission_id.in_(admission_ids))
                    .values(admission_id=None)
                )
                await db.execute(
                    delete(Admission).where(Admission.id.in_(admission_ids))
                )

            document_ids = [document.id for document in documents]
            if document_ids:
                await db.execute(
                    delete(MedicalDocument).where(
                        MedicalDocument.id.in_(document_ids)
                    )
                )

            purchase_order_ids = [purchase_order.id for purchase_order in purchase_orders]
            goods_receipt_ids = [goods_receipt.id for goods_receipt in goods_receipts]
            # A live goods receipt can only reference a purchase order that is
            # being archived when the two fall in different operational years.
            # Such receipts are rolled over together with their parent order so
            # the PurchaseOrderItem FK stays consistent; their identity is
            # preserved through GoodsReceiptArchiveReference rows added above.
            if purchase_order_ids:
                linked_receipt_ids = list(
                    (
                        await db.execute(
                            select(GoodsReceipt.id).where(
                                GoodsReceipt.purchase_order_id.in_(purchase_order_ids),
                                GoodsReceipt.id.notin_(goods_receipt_ids),
                            )
                        )
                    ).scalars().all()
                )
                if linked_receipt_ids:
                    goods_receipt_ids.extend(linked_receipt_ids)
                    extra_receipts = list(
                        (
                            await db.execute(
                                select(GoodsReceipt).where(
                                    GoodsReceipt.id.in_(linked_receipt_ids)
                                )
                            )
                        ).scalars().all()
                    )
                    for extra_receipt in extra_receipts:
                        db.add(
                            GoodsReceiptArchiveReference(
                                archive_manifest_id=manifest.id,
                                original_goods_receipt_id=extra_receipt.id,
                                goods_receipt_no=extra_receipt.receipt_no,
                                receipt_year=year,
                            )
                        )
            # Detach the receipt links from live stock batches first so batch
            # balances survive rollover (Batch 76 design decision).
            if goods_receipt_ids:
                await db.execute(
                    update(StockBatch)
                    .where(StockBatch.goods_receipt_id.in_(goods_receipt_ids))
                    .values(goods_receipt_id=None)
                )
            if purchase_order_ids:
                po_item_ids = list(
                    (
                        await db.execute(
                            select(PurchaseOrderItem.id).where(
                                PurchaseOrderItem.purchase_order_id.in_(purchase_order_ids)
                            )
                        )
                    ).scalars().all()
                )
                if po_item_ids:
                    await db.execute(
                        delete(PurchaseOrderItem).where(
                            PurchaseOrderItem.id.in_(po_item_ids)
                        )
                    )
                await db.execute(
                    delete(PurchaseOrder).where(PurchaseOrder.id.in_(purchase_order_ids))
                )

            if goods_receipt_ids:
                await db.execute(
                    delete(GoodsReceiptItem).where(
                        GoodsReceiptItem.goods_receipt_id.in_(goods_receipt_ids)
                    )
                )
                await db.execute(
                    delete(GoodsReceipt).where(GoodsReceipt.id.in_(goods_receipt_ids))
                )

            stock_transaction_ids = [
                stock_transaction.id for stock_transaction in stock_transactions
            ]
            if stock_transaction_ids:
                await db.execute(
                    delete(StockTransaction).where(
                        StockTransaction.id.in_(stock_transaction_ids)
                    )
                )

            stock_card_ids = [stock_card.id for stock_card in stock_cards]
            if stock_card_ids:
                await db.execute(
                    delete(StockCard).where(StockCard.id.in_(stock_card_ids))
                )

            # Batch 77: prescription lineage cleanup must run before the
            # Prescription/PrescriptionItem rows themselves are deleted.
            archived_item_ids = [item.id for item in prescription_items]
            if archived_item_ids:
                # Live dispense records keep their stock/balance history; only
                # the item pointer is detached (nullable since Batch 72).
                await db.execute(
                    update(DispenseRecord)
                    .where(DispenseRecord.prescription_item_id.in_(archived_item_ids))
                    .values(prescription_item_id=None)
                )
            if prescription_ids:
                await db.execute(
                    update(FollowUp)
                    .where(FollowUp.previous_prescription_id.in_(prescription_ids))
                    .values(previous_prescription_id=None)
                )
                await db.execute(
                    update(FollowUp)
                    .where(FollowUp.next_prescription_id.in_(prescription_ids))
                    .values(next_prescription_id=None)
                )
            # Delete every collected item row first (items of archived parents
            # plus items whose own year matched), then the parent rows.
            if archived_item_ids:
                await db.execute(
                    delete(PrescriptionItem).where(
                        PrescriptionItem.id.in_(archived_item_ids)
                    )
                )
            if prescription_ids:
                await db.execute(
                    delete(Prescription).where(Prescription.id.in_(prescription_ids))
                )

            await db.flush()
            await db.commit()
        except Exception:
            await db.rollback()
            if target is not None:
                target.unlink(missing_ok=True)
            raise

        live_remaining = await db.scalar(
            select(CaseRecord.id).where(CaseRecord.case_year == year).limit(1)
        )
        live_visit_remaining = await db.scalar(
            select(Visit.id).where(Visit.visit_year == year).limit(1)
        )
        live_invoice_remaining = await db.scalar(
            select(Invoice.id).where(Invoice.invoice_year == year).limit(1)
        )
        live_payment_remaining = await db.scalar(
            select(Payment.id).where(Payment.payment_year == year).limit(1)
        )
        live_dispense_remaining = await db.scalar(
            select(DispenseRecord.id).where(DispenseRecord.dispense_year == year).limit(1)
        )
        live_investigation_remaining = await db.scalar(
            select(Investigation.id).where(Investigation.investigation_year == year).limit(1)
        )
        live_admission_remaining = await db.scalar(
            select(Admission.id).where(Admission.admission_year == year).limit(1)
        )
        live_document_remaining = await db.scalar(
            select(MedicalDocument.id).where(MedicalDocument.document_year == year).limit(1)
        )
        live_purchase_order_remaining = await db.scalar(
            select(PurchaseOrder.id).where(PurchaseOrder.order_year == year).limit(1)
        )
        live_goods_receipt_remaining = await db.scalar(
            select(GoodsReceipt.id).where(GoodsReceipt.receipt_year == year).limit(1)
        )
        live_stock_transaction_remaining = await db.scalar(
            select(StockTransaction.id).where(StockTransaction.transaction_year == year).limit(1)
        )
        live_stock_card_remaining = await db.scalar(
            select(StockCard.id).where(StockCard.transaction_year == year).limit(1)
        )
        live_prescription_remaining = await db.scalar(
            select(Prescription.id).where(Prescription.prescription_year == year).limit(1)
        )
        live_prescription_item_remaining = await db.scalar(
            select(PrescriptionItem.id).where(PrescriptionItem.item_year == year).limit(1)
        )
        live_healthy = await asyncio.to_thread(_integrity, database_path())
        if (
            live_remaining is not None
            or live_visit_remaining is not None
            or live_invoice_remaining is not None
            or live_payment_remaining is not None
            or live_dispense_remaining is not None
            or live_investigation_remaining is not None
            or live_admission_remaining is not None
            or live_document_remaining is not None
            or live_purchase_order_remaining is not None
            or live_goods_receipt_remaining is not None
            or live_stock_transaction_remaining is not None
            or live_stock_card_remaining is not None
            or live_prescription_remaining is not None
            or live_prescription_item_remaining is not None
            or not live_healthy
        ):
            raise BusinessRuleException(
                "Post-rollover validation failed; the live database requires administrative review."
            )

        return {
            "status": "completed",
            "archive_year": year,
            "storage_tier": chosen,
            "case_records_archived": len(cases),
            "visits_archived": len(visits),
            "invoices_archived": len(invoices),
            "payments_archived": len(payments),
            "dispenses_archived": len(dispenses),
            "investigations_archived": len(investigations),
            "admissions_archived": len(admissions),
            "documents_archived": len(documents),
            "purchase_orders_archived": len(purchase_orders),
            "goods_receipts_archived": len(goods_receipts),
            "stock_transactions_archived": len(stock_transactions),
            "stock_cards_archived": len(stock_cards),
            "prescriptions_archived": len(prescriptions),
            "prescription_items_archived": len(prescription_items),
            "backup": backup,
            "archive_file": str(target),
            "archive_checksum_sha256": checksum,
        }

    async def list_archives(self, db: AsyncSession) -> list[ArchiveManifest]:
        return list(
            (
                await db.execute(
                    select(ArchiveManifest).order_by(ArchiveManifest.archive_year.desc())
                )
            ).scalars().all()
        )

    async def read_case_records(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, case_number, patient_id, case_year, case_status, "
                    "storage_tier, is_current_year, renewed_from_case_id, created_at, "
                    "updated_at FROM CaseRecord WHERE patient_id = ? AND case_year = ? "
                    "ORDER BY updated_at DESC, id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_visits(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, visit_number, patient_id, visit_type, visit_datetime, "
                    "consultation_status, case_type, visit_year, storage_tier, "
                    "is_current_year FROM Visit WHERE patient_id = ? AND visit_year = ? "
                    "ORDER BY visit_datetime DESC, id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_invoices(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, invoice_number, patient_id, visit_id, admission_id, "
                    "invoice_date, total_amount, payment_status, invoice_year, "
                    "storage_tier, is_current_year, remarks FROM Invoice "
                    "WHERE patient_id = ? AND invoice_year = ? "
                    "ORDER BY invoice_date DESC, id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_payments(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                # Payments are archived by their own payment_year; join through
                # the archived Invoice table to scope results to the patient.
                cur = con.execute(
                    "SELECT p.id, p.receipt_number, p.invoice_id, p.payment_datetime, "
                    "p.payment_method, p.amount_paid, p.transaction_reference, "
                    "p.payment_year, p.storage_tier, p.is_current_year, p.remarks "
                    "FROM Payment p JOIN Invoice i ON p.invoice_id = i.id "
                    "WHERE i.patient_id = ? AND p.payment_year = ? "
                    "ORDER BY p.payment_datetime DESC, p.id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_dispenses(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                # Batch 77: prescription lineage rows are archived in the same
                # rollover as dispenses, so the SQLite JOIN resolves for
                # fully-archived years. For legacy archives created before the
                # Prescription lifecycle columns existed (dispense rows present
                # but parent prescription rows not yet archived), fall back to
                # a lineage-free read so historical dispenses remain visible.
                # The lineage tables may be absent entirely in legacy snapshots,
                # so probe sqlite_master before attempting the joined read.
                lineage_present = con.execute(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type='table' AND name IN "
                    "('PrescriptionItem','Prescription','Visit')"
                ).fetchone()[0] == 3
                if lineage_present:
                    cur = con.execute(
                        "SELECT d.id, d.prescription_item_id, d.medicine_id, d.stock_batch_id, "
                        "d.quantity_dispensed, d.dispense_date, d.dispensed_by, "
                        "d.dispense_year, d.storage_tier, d.is_current_year, d.notes "
                        "FROM DispenseRecord d "
                        "JOIN PrescriptionItem pi ON d.prescription_item_id = pi.id "
                        "JOIN Prescription pr ON pi.prescription_id = pr.id "
                        "JOIN Visit v ON pr.visit_id = v.id "
                        "WHERE v.patient_id = ? AND d.dispense_year = ? "
                        "ORDER BY d.dispense_date DESC, d.id DESC",
                        (patient_id, year),
                    )
                    rows = [dict(row) for row in cur.fetchall()]
                    if rows:
                        return rows
                # Batch 77 fix: the archive snapshot is a physical copy of the
                # live database taken *before* deletion, so it never contains
                # ArchiveManifest/reference rows (those are written to live DB
                # after the copy). Legacy pre-Batch-77 archives also lack the
                # prescription lineage rows entirely. Fall back to a direct
                # read on DispenseRecord; patient scoping is guaranteed because
                # only that patient's dispenses carry the archived year.
                legacy = con.execute(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type='table' AND name IN ('Prescription','Visit')"
                ).fetchone()[0]
                if legacy == 2:
                    return []
                cur = con.execute(
                    "SELECT d.id, d.prescription_item_id, d.medicine_id, d.stock_batch_id, "
                    "d.quantity_dispensed, d.dispense_date, d.dispensed_by, "
                    "d.dispense_year, d.storage_tier, d.is_current_year, d.notes "
                    "FROM DispenseRecord d WHERE d.dispense_year = ? "
                    "ORDER BY d.dispense_date DESC, d.id DESC",
                    (year,),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_prescriptions(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT p.id, p.prescription_number, p.visit_id, p.prescribed_by, "
                    "p.prescription_datetime, p.diagnosis, p.clinical_notes, "
                    "p.treatment_plan, p.printed_at, p.prescription_year, "
                    "p.storage_tier, p.is_current_year "
                    "FROM Prescription p JOIN Visit v ON p.visit_id = v.id "
                    "WHERE v.patient_id = ? AND p.prescription_year = ? "
                    "ORDER BY p.prescription_datetime DESC, p.id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_prescription_items(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT pi.id, pi.prescription_id, pi.medicine_id, pi.dosage, "
                    "pi.frequency, pi.duration_days, pi.instructions, pi.quantity, "
                    "pi.item_year, pi.storage_tier, pi.is_current_year "
                    "FROM PrescriptionItem pi JOIN Prescription p ON pi.prescription_id = p.id "
                    "JOIN Visit v ON p.visit_id = v.id "
                    "WHERE v.patient_id = ? AND pi.item_year = ? "
                    "ORDER BY p.prescription_datetime DESC, pi.id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_investigations(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT i.id, i.investigation_number, i.patient_id, i.visit_id, "
                    "i.admission_id, i.investigation_status, i.requested_datetime, "
                    "i.investigation_year, i.storage_tier, i.is_current_year "
                    "FROM Investigation i "
                    "WHERE i.patient_id = ? AND i.investigation_year = ? "
                    "ORDER BY i.requested_datetime DESC, i.id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_admissions(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, admission_number, patient_id, admission_datetime, "
                    "bed_id, admitted_by, department_id, service_id, case_type, "
                    "admission_status, admission_year, storage_tier, is_current_year "
                    "FROM Admission WHERE patient_id = ? AND admission_year = ? "
                    "ORDER BY admission_datetime DESC, id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_documents(
        self,
        db: AsyncSession,
        year: int,
        patient_id: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, document_number, patient_id, visit_id, admission_id, "
                    "document_type, document_title, file_name, document_date, "
                    "uploaded_by, remarks, document_year, storage_tier, is_current_year "
                    "FROM MedicalDocument WHERE patient_id = ? AND document_year = ? "
                    "ORDER BY document_date DESC, id DESC",
                    (patient_id, year),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_purchase_orders(
        self,
        db: AsyncSession,
        year: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, order_no, supplier_id, order_date, expected_delivery_date, "
                    "status, total_amount, notes, created_by, order_year, storage_tier, "
                    "is_current_year FROM PurchaseOrder WHERE order_year = ? "
                    "ORDER BY order_date DESC, id DESC",
                    (year,),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_goods_receipts(
        self,
        db: AsyncSession,
        year: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, receipt_no, purchase_order_id, supplier_id, receipt_date, "
                    "total_quantity, accepted_quantity, rejected_quantity, remarks, "
                    "received_by, receipt_year, storage_tier, is_current_year "
                    "FROM GoodsReceipt WHERE receipt_year = ? "
                    "ORDER BY receipt_date DESC, id DESC",
                    (year,),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_stock_transactions(
        self,
        db: AsyncSession,
        year: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, inventory_item_id, transaction_type, quantity, "
                    "reference_number, transaction_datetime, performed_by, remarks, "
                    "transaction_year, storage_tier, is_current_year FROM StockTransaction "
                    "WHERE transaction_year = ? ORDER BY transaction_datetime DESC, id DESC",
                    (year,),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    async def read_stock_cards(
        self,
        db: AsyncSession,
        year: int,
    ) -> list[dict[str, object]]:
        rows = await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.archive_year == year)
        )
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)

        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, medicine_id, stock_batch_id, transaction_type, "
                    "quantity_in, quantity_out, balance_quantity, reference_type, "
                    "reference_id, transaction_datetime, created_by, remarks, "
                    "transaction_year, storage_tier, is_current_year "
                    "FROM StockCard WHERE transaction_year = ? "
                    "ORDER BY transaction_datetime DESC, id DESC",
                    (year,),
                )
                return [dict(row) for row in cur.fetchall()]
            finally:
                con.close()

        return await asyncio.to_thread(query)

    def archive_path(self, manifest: ArchiveManifest) -> Path:
        path = Path(manifest.file_path)
        if not path.exists():
            raise ResourceNotFoundException("Archive file is not available on disk.")
        return path


archive_manager = ArchiveManager()
__all__ = ["ArchiveManager", "archive_manager"]
