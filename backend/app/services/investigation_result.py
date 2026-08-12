"""
HHMS Investigation Result Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.investigation import Investigation
from app.models.investigation_result import (
    InvestigationResult,
)
from app.repositories.investigation_result import (
    InvestigationResultRepository,
    investigation_result_repository,
)
from app.schemas.investigation_result import (
    InvestigationResultCreate,
    InvestigationResultUpdate,
)


class InvestigationResultService:
    """Business workflows for laboratory results."""

    def __init__(
        self,
        repository: (
            InvestigationResultRepository | None
        ) = None,
    ) -> None:
        self.repository = (
            repository
            or investigation_result_repository
        )

    async def get(
        self,
        db: AsyncSession,
        result_id: int,
    ) -> InvestigationResult:
        result = await self.repository.get_by_id(
            db,
            result_id,
        )

        if result is None:
            raise ResourceNotFoundException(
                "Investigation result not found."
            )

        return result

    async def get_by_investigation(
        self,
        db: AsyncSession,
        investigation_id: int,
    ) -> InvestigationResult:
        result = (
            await self.repository
            .get_by_investigation(
                db,
                investigation_id,
            )
        )

        if result is None:
            raise ResourceNotFoundException(
                "Investigation result not found."
            )

        return result

    async def list(
        self,
        db: AsyncSession,
        *,
        investigation_id: int | None = None,
        report_status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InvestigationResult]:
        return await self.repository.list_all(
            db,
            investigation_id=investigation_id,
            report_status=report_status,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: InvestigationResultCreate,
    ) -> InvestigationResult:
        investigation = await db.get(
            Investigation,
            data.investigation_id,
        )

        if investigation is None:
            raise ResourceNotFoundException(
                "Investigation not found."
            )

        if (
            investigation.investigation_status
            == "cancelled"
        ):
            raise BusinessRuleException(
                "A result cannot be recorded for "
                "a cancelled investigation."
            )

        existing = (
            await self.repository
            .get_by_investigation(
                db,
                data.investigation_id,
            )
        )

        if existing is not None:
            raise DuplicateResourceException(
                "This investigation already has a result."
            )

        now = datetime.now(timezone.utc)

        result = InvestigationResult(
            investigation_id=(
                data.investigation_id
            ),
            result_text=data.result_text,
            interpretation=data.interpretation,
            result_datetime=(
                data.result_datetime
            ),
            verified_by=data.verified_by,
            verification_datetime=(
                data.verification_datetime
            ),
            report_status=data.report_status,
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            result = await self.repository.add(
                db,
                result,
            )

            if (
                result.report_status
                == "released"
            ):
                investigation.investigation_status = (
                    "completed"
                )

            elif (
                investigation.investigation_status
                == "pending"
            ):
                investigation.investigation_status = (
                    "in_progress"
                )

            investigation.updated_at = now

            await db.commit()

            return result

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create investigation result."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create investigation result."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        result_id: int,
        data: InvestigationResultUpdate,
    ) -> InvestigationResult:
        result = await self.get(
            db,
            result_id,
        )

        investigation = await db.get(
            Investigation,
            result.investigation_id,
        )

        if investigation is None:
            raise ResourceNotFoundException(
                "Source investigation not found."
            )

        if result.report_status == "released":
            raise BusinessRuleException(
                "A released laboratory report cannot "
                "be modified."
            )

        values = data.model_dump(
            exclude_unset=True,
        )

        target_status = values.get(
            "report_status",
            result.report_status,
        )

        target_verified_by = values.get(
            "verified_by",
            result.verified_by,
        )

        target_verification_datetime = values.get(
            "verification_datetime",
            result.verification_datetime,
        )

        if target_status in {
            "verified",
            "released",
        }:
            if target_verified_by is None:
                raise BusinessRuleException(
                    "verified_by is required for a "
                    "verified or released report."
                )

            if target_verification_datetime is None:
                raise BusinessRuleException(
                    "verification_datetime is required "
                    "for a verified or released report."
                )

        for field, value in values.items():
            setattr(
                result,
                field,
                value,
            )

        now = datetime.now(timezone.utc)

        result.updated_at = now

        if target_status == "released":
            investigation.investigation_status = (
                "completed"
            )

        elif target_status == "verified":
            investigation.investigation_status = (
                "in_progress"
            )

        elif (
            investigation.investigation_status
            == "pending"
        ):
            investigation.investigation_status = (
                "in_progress"
            )

        investigation.updated_at = now

        try:
            await db.commit()
            await db.refresh(result)

            return result

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update investigation result."
            ) from exc

    async def delete(
        self,
        db: AsyncSession,
        result_id: int,
    ) -> InvestigationResult:
        result = await self.get(
            db,
            result_id,
        )

        raise BusinessRuleException(
            "Investigation results are permanent clinical "
            "records and cannot be deleted."
        )


investigation_result_service = (
    InvestigationResultService()
)


__all__ = [
    "InvestigationResultService",
    "investigation_result_service",
]