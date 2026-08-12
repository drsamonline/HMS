"""Hospital statistics service.

The service treats clinical source records as the canonical activity sources:
Visit, Admission and Investigation. Generic ServiceActivity rows are added
for configurable departments/services that have no dedicated clinical table.

A ServiceActivity row carrying source_type/source_id for a Visit, Admission or
Investigation is treated as a projection of that source record and is excluded
from aggregate counts. This prevents double-counting.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import String, and_, case, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admission import Admission
from app.models.department import Department
from app.models.department_service import DepartmentService
from app.models.investigation import Investigation
from app.models.patient import Patient
from app.models.service_activity import ServiceActivity
from app.models.visit import Visit
from app.schemas.statistics import (
    DepartmentStatistics,
    HospitalStatistics,
    ServiceStatistics,
)


_CANONICAL_SOURCE_TYPES = ("visit", "admission", "investigation")


def _period_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    if end_date < start_date:
        raise ValueError("end_date cannot be earlier than start_date.")
    return (
        datetime.combine(start_date, time.min),
        datetime.combine(end_date + timedelta(days=1), time.min),
    )


def _activity_selects(start: datetime, end: datetime):
    visit = select(
        Visit.patient_id.label("patient_id"),
        Visit.department_id.label("department_id"),
        Visit.service_id.label("service_id"),
        Visit.visit_datetime.label("activity_datetime"),
        Visit.case_type.label("case_type"),
        func.cast(None, String).label("fulfillment_mode"),
        literal("opd").label("activity_type"),
        literal("visit").label("source_type"),
        Visit.id.label("source_id"),
    ).where(
        Visit.visit_datetime >= start,
        Visit.visit_datetime < end,
    )

    admission = select(
        Admission.patient_id.label("patient_id"),
        Admission.department_id.label("department_id"),
        Admission.service_id.label("service_id"),
        Admission.admission_datetime.label("activity_datetime"),
        Admission.case_type.label("case_type"),
        func.cast(None, String).label("fulfillment_mode"),
        literal("ipd").label("activity_type"),
        literal("admission").label("source_type"),
        Admission.id.label("source_id"),
    ).where(
        Admission.admission_datetime >= start,
        Admission.admission_datetime < end,
    )

    investigation = select(
        Investigation.patient_id.label("patient_id"),
        Investigation.department_id.label("department_id"),
        Investigation.service_id.label("service_id"),
        Investigation.requested_datetime.label("activity_datetime"),
        Investigation.case_type.label("case_type"),
        Investigation.fulfillment_mode.label("fulfillment_mode"),
        literal("investigation").label("activity_type"),
        literal("investigation").label("source_type"),
        Investigation.id.label("source_id"),
    ).where(
        Investigation.requested_datetime >= start,
        Investigation.requested_datetime < end,
    )

    generic = select(
        ServiceActivity.patient_id.label("patient_id"),
        ServiceActivity.department_id.label("department_id"),
        ServiceActivity.service_id.label("service_id"),
        ServiceActivity.activity_datetime.label("activity_datetime"),
        ServiceActivity.case_type.label("case_type"),
        ServiceActivity.fulfillment_mode.label("fulfillment_mode"),
        literal("service").label("activity_type"),
        ServiceActivity.source_type.label("source_type"),
        ServiceActivity.source_id.label("source_id"),
    ).where(
        ServiceActivity.activity_datetime >= start,
        ServiceActivity.activity_datetime < end,
        or_(
            ServiceActivity.source_type.is_(None),
            ~and_(
                ServiceActivity.source_type.in_(_CANONICAL_SOURCE_TYPES),
                ServiceActivity.source_id.is_not(None),
            ),
        ),
    )

    return union_all(visit, admission, investigation, generic).subquery("activities")


class StatisticsService:
    """Build deduplicated hospital and departmental statistics."""

    async def get_hospital_statistics(
        self,
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
        department_id: UUID | None = None,
        service_id: UUID | None = None,
    ) -> HospitalStatistics:
        start, end = _period_bounds(start_date, end_date)
        activities = _activity_selects(start, end)

        filters: list[Any] = []
        if department_id is not None:
            filters.append(activities.c.department_id == department_id)
        if service_id is not None:
            filters.append(activities.c.service_id == service_id)

        activity_scope = select(activities).where(*filters).subquery("activity_scope")

        unique_patients_stmt = (
            select(func.count(func.distinct(activity_scope.c.patient_id)))
        )
        unique_patient_count = int((await db.scalar(unique_patients_stmt)) or 0)

        rows = (
            await db.execute(
                select(
                    func.count().label("total"),
                    func.sum(
                        case((activity_scope.c.activity_type == "opd", 1), else_=0)
                    ).label("opd"),
                    func.sum(
                        case((activity_scope.c.activity_type == "ipd", 1), else_=0)
                    ).label("ipd"),
                    func.sum(
                        case(
                            (activity_scope.c.activity_type == "investigation", 1),
                            else_=0,
                        )
                    ).label("investigation"),
                    func.sum(
                        case(
                            (activity_scope.c.activity_type == "service", 1),
                            else_=0,
                        )
                    ).label("service"),
                    func.sum(
                        case((activity_scope.c.case_type == "new", 1), else_=0)
                    ).label("new_case"),
                    func.sum(
                        case((activity_scope.c.case_type == "old", 1), else_=0)
                    ).label("old_case"),
                    func.sum(
                        case(
                            (
                                and_(
                                    activity_scope.c.activity_type == "investigation",
                                    func.lower(
                                        func.coalesce(
                                            activity_scope.c.fulfillment_mode, ""
                                        )
                                    ).in_(("inhouse", "in-house", "in_house")),
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("inhouse"),
                    func.sum(
                        case(
                            (
                                and_(
                                    activity_scope.c.activity_type == "investigation",
                                    func.lower(
                                        func.coalesce(
                                            activity_scope.c.fulfillment_mode, ""
                                        )
                                    )
                                    == "outsourced",
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("outsourced"),
                )
            )
        ).one()

        demographic_rows = await db.execute(
            select(
                func.count(func.distinct(Patient.id)).label("total"),
                func.count(
                    func.distinct(
                        case(
                            (func.lower(Patient.gender) == "male", Patient.id),
                            else_=None,
                        )
                    )
                ).label("male"),
                func.count(
                    func.distinct(
                        case(
                            (func.lower(Patient.gender) == "female", Patient.id),
                            else_=None,
                        )
                    )
                ).label("female"),
                func.count(
                    func.distinct(
                        case(
                            (
                                ~func.lower(Patient.gender).in_(("male", "female")),
                                Patient.id,
                            ),
                            else_=None,
                        )
                    )
                ).label("other_gender"),
                func.count(
                    func.distinct(
                        case(
                            (and_(Patient.age.is_not(None), Patient.age < 18), Patient.id),
                            else_=None,
                        )
                    )
                ).label("child"),
                func.count(
                    func.distinct(
                        case(
                            (and_(Patient.age.is_not(None), Patient.age >= 18), Patient.id),
                            else_=None,
                        )
                    )
                ).label("adult"),
                func.count(
                    func.distinct(
                        case((Patient.age.is_(None), Patient.id), else_=None)
                    )
                ).label("unknown_age"),
            )
            .join(activity_scope, activity_scope.c.patient_id == Patient.id)
        )
        demo = demographic_rows.one()

        departments = await self._department_stats(db, activity_scope)
        services = await self._service_stats(db, activity_scope)

        return HospitalStatistics(
            start_date=start_date,
            end_date=end_date,
            unique_hospital_patient_count=unique_patient_count,
            total_activity_count=int(rows.total or 0),
            opd_count=int(rows.opd or 0),
            ipd_count=int(rows.ipd or 0),
            investigation_count=int(rows.investigation or 0),
            generic_service_count=int(rows.service or 0),
            male_patient_count=int(demo.male or 0),
            female_patient_count=int(demo.female or 0),
            other_gender_patient_count=int(demo.other_gender or 0),
            child_patient_count=int(demo.child or 0),
            adult_patient_count=int(demo.adult or 0),
            unspecified_age_patient_count=int(demo.unknown_age or 0),
            new_case_activity_count=int(rows.new_case or 0),
            old_case_activity_count=int(rows.old_case or 0),
            unspecified_case_activity_count=(
                int(rows.total or 0) - int(rows.new_case or 0) - int(rows.old_case or 0)
            ),
            inhouse_investigation_count=int(rows.inhouse or 0),
            outsourced_investigation_count=int(rows.outsourced or 0),
            departments=departments,
            services=services,
        )

    async def _department_stats(
        self, db: AsyncSession, activity_scope
    ) -> list[DepartmentStatistics]:
        stmt = (
            select(
                Department.id.label("department_id"),
                Department.name.label("department_name"),
                func.count().label("activity_count"),
                func.count(func.distinct(activity_scope.c.patient_id)).label("unique_patients"),
                func.sum(case((activity_scope.c.activity_type == "opd", 1), else_=0)).label("opd"),
                func.sum(case((activity_scope.c.activity_type == "ipd", 1), else_=0)).label("ipd"),
                func.sum(
                    case((activity_scope.c.activity_type == "investigation", 1), else_=0)
                ).label("investigation"),
                func.sum(case((activity_scope.c.activity_type == "service", 1), else_=0)).label("service"),
                func.sum(case((func.lower(Patient.gender) == "male", 1), else_=0)).label("male"),
                func.sum(case((func.lower(Patient.gender) == "female", 1), else_=0)).label("female"),
                func.sum(
                    case(
                        (~func.lower(Patient.gender).in_(("male", "female")), 1),
                        else_=0,
                    )
                ).label("other_gender"),
                func.sum(case((and_(Patient.age.is_not(None), Patient.age < 18), 1), else_=0)).label("child"),
                func.sum(case((and_(Patient.age.is_not(None), Patient.age >= 18), 1), else_=0)).label("adult"),
                func.sum(case((Patient.age.is_(None), 1), else_=0)).label("unknown_age"),
                func.sum(case((activity_scope.c.case_type == "new", 1), else_=0)).label("new_case"),
                func.sum(case((activity_scope.c.case_type == "old", 1), else_=0)).label("old_case"),
                func.sum(
                    case(
                        (
                            and_(
                                activity_scope.c.activity_type == "investigation",
                                func.lower(func.coalesce(activity_scope.c.fulfillment_mode, "")).in_(
                                    ("inhouse", "in-house", "in_house")
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("inhouse"),
                func.sum(
                    case(
                        (
                            and_(
                                activity_scope.c.activity_type == "investigation",
                                func.lower(func.coalesce(activity_scope.c.fulfillment_mode, ""))
                                == "outsourced",
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("outsourced"),
            )
            .join(activity_scope, activity_scope.c.department_id == Department.id)
            .join(Patient, Patient.id == activity_scope.c.patient_id)
            .group_by(Department.id, Department.name)
            .order_by(Department.name)
        )
        result = await db.execute(stmt)
        return [
            DepartmentStatistics(
                department_id=r.department_id,
                department_name=r.department_name,
                activity_count=int(r.activity_count or 0),
                unique_patient_count=int(r.unique_patients or 0),
                opd_count=int(r.opd or 0),
                ipd_count=int(r.ipd or 0),
                investigation_count=int(r.investigation or 0),
                service_count=int(r.service or 0),
                male_count=int(r.male or 0),
                female_count=int(r.female or 0),
                other_gender_count=int(r.other_gender or 0),
                child_count=int(r.child or 0),
                adult_count=int(r.adult or 0),
                unspecified_age_count=int(r.unknown_age or 0),
                new_case_count=int(r.new_case or 0),
                old_case_count=int(r.old_case or 0),
                unspecified_case_count=int(r.activity_count or 0) - int(r.new_case or 0) - int(r.old_case or 0),
                inhouse_count=int(r.inhouse or 0),
                outsourced_count=int(r.outsourced or 0),
            )
            for r in result
        ]

    async def _service_stats(
        self, db: AsyncSession, activity_scope
    ) -> list[ServiceStatistics]:
        stmt = (
            select(
                DepartmentService.id.label("service_id"),
                DepartmentService.name.label("service_name"),
                Department.id.label("department_id"),
                Department.name.label("department_name"),
                func.count().label("activity_count"),
                func.count(func.distinct(activity_scope.c.patient_id)).label("unique_patients"),
                func.sum(case((func.lower(Patient.gender) == "male", 1), else_=0)).label("male"),
                func.sum(case((func.lower(Patient.gender) == "female", 1), else_=0)).label("female"),
                func.sum(
                    case((~func.lower(Patient.gender).in_(("male", "female")), 1), else_=0)
                ).label("other_gender"),
                func.sum(case((and_(Patient.age.is_not(None), Patient.age < 18), 1), else_=0)).label("child"),
                func.sum(case((and_(Patient.age.is_not(None), Patient.age >= 18), 1), else_=0)).label("adult"),
                func.sum(case((Patient.age.is_(None), 1), else_=0)).label("unknown_age"),
                func.sum(case((activity_scope.c.case_type == "new", 1), else_=0)).label("new_case"),
                func.sum(case((activity_scope.c.case_type == "old", 1), else_=0)).label("old_case"),
                func.sum(
                    case(
                        (
                            func.lower(func.coalesce(activity_scope.c.fulfillment_mode, "")).in_(
                                ("inhouse", "in-house", "in_house")
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("inhouse"),
                func.sum(
                    case(
                        (func.lower(func.coalesce(activity_scope.c.fulfillment_mode, "")) == "outsourced", 1),
                        else_=0,
                    )
                ).label("outsourced"),
            )
            .join(DepartmentService, activity_scope.c.service_id == DepartmentService.id)
            .join(Department, DepartmentService.department_id == Department.id)
            .join(Patient, Patient.id == activity_scope.c.patient_id)
            .group_by(
                DepartmentService.id,
                DepartmentService.name,
                Department.id,
                Department.name,
            )
            .order_by(Department.name, DepartmentService.name)
        )
        result = await db.execute(stmt)
        return [
            ServiceStatistics(
                service_id=r.service_id,
                service_name=r.service_name,
                department_id=r.department_id,
                department_name=r.department_name,
                activity_count=int(r.activity_count or 0),
                unique_patient_count=int(r.unique_patients or 0),
                male_count=int(r.male or 0),
                female_count=int(r.female or 0),
                other_gender_count=int(r.other_gender or 0),
                child_count=int(r.child or 0),
                adult_count=int(r.adult or 0),
                unspecified_age_count=int(r.unknown_age or 0),
                new_case_count=int(r.new_case or 0),
                old_case_count=int(r.old_case or 0),
                unspecified_case_count=int(r.activity_count or 0) - int(r.new_case or 0) - int(r.old_case or 0),
                inhouse_count=int(r.inhouse or 0),
                outsourced_count=int(r.outsourced or 0),
            )
            for r in result
        ]


statistics_service = StatisticsService()

__all__ = ["StatisticsService", "statistics_service"]
