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
from app.models.diagnosis import Diagnosis
from app.models.dispense_record import DispenseRecord
from app.models.followup import FollowUp
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.investigation import Investigation
from app.models.investigation_result import InvestigationResult
from app.models.lab_archive_reference import InvestigationArchiveReference
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
        live_healthy = await asyncio.to_thread(_integrity, database_path())
        if (
            live_remaining is not None
            or live_visit_remaining is not None
            or live_invoice_remaining is not None
            or live_payment_remaining is not None
            or live_dispense_remaining is not None
            or live_investigation_remaining is not None
            or live_admission_remaining is not None
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
                # Dispense rows are archived by their own dispense_year; join
                # through the prescription lineage to scope results to the patient.
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

    def archive_path(self, manifest: ArchiveManifest) -> Path:
        path = Path(manifest.file_path)
        if not path.exists():
            raise ResourceNotFoundException("Archive file is not available on disk.")
        return path


archive_manager = ArchiveManager()
__all__ = ["ArchiveManager", "archive_manager"]
