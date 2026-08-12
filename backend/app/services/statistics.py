"""Hospital statistics reporting service.

Canonical source records are Visit, Admission and Investigation. Generic
ServiceActivity rows represent configurable departmental services. Projection
rows that point to one of the canonical source records are excluded so the
same clinical event is never counted twice.
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
    ActivityBreakdown,
    DailyStatistics,
    DepartmentStatistics,
    HospitalStatistics,
    ServiceStatistics,
    ServiceTypeStatistics,
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
    ).where(Visit.visit_datetime >= start, Visit.visit_datetime < end)

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
    ).where(Admission.admission_datetime >= start, Admission.admission_datetime < end)

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


def _apply_scope_filters(activity_scope, department_id, service_id):
    filters: list[Any] = []
    if department_id is not None:
        filters.append(activity_scope.c.department_id == department_id)
    if service_id is not None:
        filters.append(activity_scope.c.service_id == service_id)
    return filters


def _gender_counts(patient_id_column, gender_column):
    return (
        func.count(
            func.distinct(
                case((func.lower(gender_column) == "male", patient_id_column), else_=None)
            )
        ),
        func.count(
            func.distinct(
                case((func.lower(gender_column) == "female", patient_id_column), else_=None)
            )
        ),
        func.count(
            func.distinct(
                case(
                    (
                        ~func.lower(gender_column).in_(("male", "female")),
                        patient_id_column,
                    ),
                    else_=None,
                )
            )
        ),
    )


def _age_counts(patient_id_column, age_column):
    return (
        func.count(
            func.distinct(
                case((and_(age_column.is_not(None), age_column < 18), patient_id_column), else_=None)
            )
        ),
        func.count(
            func.distinct(
                case((and_(age_column.is_not(None), age_column >= 18), patient_id_column), else_=None)
            )
        ),
        func.count(
            func.distinct(case((age_column.is_(None), patient_id_column), else_=None))
        ),
    )


class StatisticsService:
    """Produce hospital, department, service and daily statistics."""

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
        filters = _apply_scope_filters(activities, department_id, service_id)
        activity_scope = select(activities).where(*filters).subquery("activity_scope")

        total_row = (
            await db.execute(
                select(
                    func.count().label("total"),
                    func.sum(case((activity_scope.c.activity_type == "opd", 1), else_=0)).label("opd"),
                    func.sum(case((activity_scope.c.activity_type == "ipd", 1), else_=0)).label("ipd"),
                    func.sum(
                        case((activity_scope.c.activity_type == "investigation", 1), else_=0)
                    ).label("investigation"),
                    func.sum(case((activity_scope.c.activity_type == "service", 1), else_=0)).label("service"),
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
            )
        ).one()

        male, female, other = _gender_counts(activity_scope.c.patient_id, Patient.gender)
        child, adult, unknown_age = _age_counts(activity_scope.c.patient_id, Patient.age)

        demo = (
            await db.execute(
                select(
                    func.count(func.distinct(activity_scope.c.patient_id)).label("total"),
                    male.label("male"),
                    female.label("female"),
                    other.label("other_gender"),
                    child.label("child"),
                    adult.label("adult"),
                    unknown_age.label("unknown_age"),
                ).join(Patient, Patient.id == activity_scope.c.patient_id)
            )
        ).one()

        departments = await self._department_stats(db, activity_scope)
        services = await self._service_stats(db, activity_scope)
        activity_breakdown, case_breakdown, fulfillment_breakdown, service_type_breakdown = (
            await self._activity_breakdowns(db, activity_scope)
        )
        daily = await self._daily_stats(db, activity_scope)

        total = int(total_row.total or 0)
        new_count = int(total_row.new_case or 0)
        old_count = int(total_row.old_case or 0)

        return HospitalStatistics(
            start_date=start_date,
            end_date=end_date,
            unique_hospital_patient_count=int(demo.total or 0),
            total_activity_count=total,
            opd_count=int(total_row.opd or 0),
            ipd_count=int(total_row.ipd or 0),
            investigation_count=int(total_row.investigation or 0),
            generic_service_count=int(total_row.service or 0),
            male_patient_count=int(demo.male or 0),
            female_patient_count=int(demo.female or 0),
            other_gender_patient_count=int(demo.other_gender or 0),
            child_patient_count=int(demo.child or 0),
            adult_patient_count=int(demo.adult or 0),
            unspecified_age_patient_count=int(demo.unknown_age or 0),
            new_case_activity_count=new_count,
            old_case_activity_count=old_count,
            unspecified_case_activity_count=max(total - new_count - old_count, 0),
            inhouse_investigation_count=int(total_row.inhouse or 0),
            outsourced_investigation_count=int(total_row.outsourced or 0),
            activity_type_breakdown=activity_breakdown,
            case_type_breakdown=case_breakdown,
            fulfillment_breakdown=fulfillment_breakdown,
            service_type_breakdown=service_type_breakdown,
            departments=departments,
            services=services,
            daily=daily,
        )

    async def _activity_breakdowns(self, db: AsyncSession, activity_scope):
        """Return activity, case-type and fulfillment-mode breakdowns."""
        activity_result = await db.execute(
            select(
                activity_scope.c.activity_type,
                func.count().label("count"),
            )
            .group_by(activity_scope.c.activity_type)
            .order_by(activity_scope.c.activity_type)
        )
        activity = [
            ActivityBreakdown(name=str(r.activity_type), count=int(r.count or 0))
            for r in activity_result
        ]

        case_result = await db.execute(
            select(
                func.coalesce(activity_scope.c.case_type, "unspecified").label("case_type"),
                func.count().label("count"),
            )
            .group_by(activity_scope.c.case_type)
            .order_by(activity_scope.c.case_type)
        )
        case_types = [
            ActivityBreakdown(name=str(r.case_type), count=int(r.count or 0))
            for r in case_result
        ]

        fulfillment_result = await db.execute(
            select(
                func.coalesce(
                    func.nullif(func.lower(activity_scope.c.fulfillment_mode), ""),
                    "unspecified",
                ).label("fulfillment_mode"),
                func.count().label("count"),
            )
            .where(activity_scope.c.activity_type == "investigation")
            .group_by(activity_scope.c.fulfillment_mode)
            .order_by(activity_scope.c.fulfillment_mode)
        )
        fulfillment = [
            ActivityBreakdown(name=str(r.fulfillment_mode), count=int(r.count or 0))
            for r in fulfillment_result
        ]

        service_type_result = await db.execute(
            select(
                func.coalesce(
                    func.nullif(DepartmentService.service_type, ""),
                    "unspecified",
                ).label("service_type"),
                func.count().label("activity_count"),
                func.count(func.distinct(activity_scope.c.patient_id)).label("unique_patients"),
            )
            .select_from(activity_scope)
            .outerjoin(
                DepartmentService,
                DepartmentService.id == activity_scope.c.service_id,
            )
            .group_by(DepartmentService.service_type)
            .order_by(DepartmentService.service_type)
        )
        service_types = [
            ServiceTypeStatistics(
                service_type=str(r.service_type),
                activity_count=int(r.activity_count or 0),
                unique_patient_count=int(r.unique_patients or 0),
            )
            for r in service_type_result
        ]
        return activity, case_types, fulfillment, service_types

    async def _department_stats(self, db: AsyncSession, activity_scope):
        """Aggregate department activity with department-local distinct demographics."""
        male = func.count(func.distinct(case((func.lower(Patient.gender) == "male", activity_scope.c.patient_id), else_=None)))
        female = func.count(func.distinct(case((func.lower(Patient.gender) == "female", activity_scope.c.patient_id), else_=None)))
        other = func.count(func.distinct(case((~func.lower(Patient.gender).in_(("male", "female")), activity_scope.c.patient_id), else_=None)))
        child = func.count(func.distinct(case((and_(Patient.age.is_not(None), Patient.age < 18), activity_scope.c.patient_id), else_=None)))
        adult = func.count(func.distinct(case((and_(Patient.age.is_not(None), Patient.age >= 18), activity_scope.c.patient_id), else_=None)))
        unknown_age = func.count(func.distinct(case((Patient.age.is_(None), activity_scope.c.patient_id), else_=None)))
        stmt = (
            select(
                Department.id.label("department_id"), Department.name.label("department_name"),
                Department.department_type.label("department_type"), func.count().label("activity_count"),
                func.count(func.distinct(activity_scope.c.patient_id)).label("unique_patients"),
                func.sum(case((activity_scope.c.activity_type == "opd", 1), else_=0)).label("opd"),
                func.sum(case((activity_scope.c.activity_type == "ipd", 1), else_=0)).label("ipd"),
                func.sum(case((activity_scope.c.activity_type == "investigation", 1), else_=0)).label("investigation"),
                func.sum(case((activity_scope.c.activity_type == "service", 1), else_=0)).label("service"),
                male.label("male"), female.label("female"), other.label("other_gender"),
                child.label("child"), adult.label("adult"), unknown_age.label("unknown_age"),
                func.sum(case((activity_scope.c.case_type == "new", 1), else_=0)).label("new_case"),
                func.sum(case((activity_scope.c.case_type == "old", 1), else_=0)).label("old_case"),
                func.sum(case((and_(activity_scope.c.activity_type == "investigation", func.lower(func.coalesce(activity_scope.c.fulfillment_mode, "")).in_(("inhouse", "in-house", "in_house"))), 1), else_=0)).label("inhouse"),
                func.sum(case((and_(activity_scope.c.activity_type == "investigation", func.lower(func.coalesce(activity_scope.c.fulfillment_mode, "")) == "outsourced"), 1), else_=0)).label("outsourced"),
            )
            .join(Department, Department.id == activity_scope.c.department_id)
            .join(Patient, Patient.id == activity_scope.c.patient_id)
            .group_by(Department.id, Department.name, Department.department_type)
            .order_by(Department.name)
        )
        result = await db.execute(stmt)
        rows=[]
        for r in result:
            total=int(r.activity_count or 0); new_count=int(r.new_case or 0); old_count=int(r.old_case or 0)
            rows.append(DepartmentStatistics(department_id=r.department_id, department_name=r.department_name, department_type=str(r.department_type or ""), activity_count=total, unique_patient_count=int(r.unique_patients or 0), opd_count=int(r.opd or 0), ipd_count=int(r.ipd or 0), investigation_count=int(r.investigation or 0), service_count=int(r.service or 0), male_count=int(r.male or 0), female_count=int(r.female or 0), other_gender_count=int(r.other_gender or 0), child_count=int(r.child or 0), adult_count=int(r.adult or 0), unspecified_age_count=int(r.unknown_age or 0), new_case_count=new_count, old_case_count=old_count, unspecified_case_count=max(total-new_count-old_count,0), inhouse_count=int(r.inhouse or 0), outsourced_count=int(r.outsourced or 0)))
        return rows

    async def _service_stats(self, db: AsyncSession, activity_scope):
        """Aggregate service activity with service-local distinct demographics."""
        male = func.count(func.distinct(case((func.lower(Patient.gender) == "male", activity_scope.c.patient_id), else_=None)))
        female = func.count(func.distinct(case((func.lower(Patient.gender) == "female", activity_scope.c.patient_id), else_=None)))
        other = func.count(func.distinct(case((~func.lower(Patient.gender).in_(("male", "female")), activity_scope.c.patient_id), else_=None)))
        child = func.count(func.distinct(case((and_(Patient.age.is_not(None), Patient.age < 18), activity_scope.c.patient_id), else_=None)))
        adult = func.count(func.distinct(case((and_(Patient.age.is_not(None), Patient.age >= 18), activity_scope.c.patient_id), else_=None)))
        unknown_age = func.count(func.distinct(case((Patient.age.is_(None), activity_scope.c.patient_id), else_=None)))
        stmt = (
            select(
                DepartmentService.id.label("service_id"),
                DepartmentService.name.label("service_name"),
                Department.id.label("department_id"),
                Department.name.label("department_name"),
                Department.department_type.label("department_type"),
                DepartmentService.service_type.label("service_type"),
                func.count().label("activity_count"),
                func.count(func.distinct(activity_scope.c.patient_id)).label("unique_patients"),
                male.label("male"),
                female.label("female"),
                other.label("other_gender"),
                child.label("child"),
                adult.label("adult"),
                unknown_age.label("unknown_age"),
                func.sum(case((activity_scope.c.activity_type == "opd", 1), else_=0)).label("opd"),
                func.sum(case((activity_scope.c.activity_type == "ipd", 1), else_=0)).label("ipd"),
                func.sum(case((activity_scope.c.activity_type == "investigation", 1), else_=0)).label("investigation"),
                func.sum(case((activity_scope.c.activity_type == "service", 1), else_=0)).label("service"),
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
            .join(DepartmentService, DepartmentService.id == activity_scope.c.service_id)
            .join(Department, Department.id == DepartmentService.department_id)
            .join(Patient, Patient.id == activity_scope.c.patient_id)
            .group_by(
                DepartmentService.id,
                DepartmentService.name,
                DepartmentService.service_type,
                Department.id,
                Department.name,
                Department.department_type,
            )
            .order_by(Department.name, DepartmentService.name)
        )
        result = await db.execute(stmt)
        rows = []
        for r in result:
            total = int(r.activity_count or 0)
            new_count = int(r.new_case or 0)
            old_count = int(r.old_case or 0)
            rows.append(
                ServiceStatistics(
                    service_id=r.service_id,
                    service_name=r.service_name,
                    department_id=r.department_id,
                    department_name=r.department_name,
                    department_type=str(r.department_type or ""),
                    activity_count=total,
                    unique_patient_count=int(r.unique_patients or 0),
                    male_count=int(r.male or 0),
                    female_count=int(r.female or 0),
                    other_gender_count=int(r.other_gender or 0),
                    child_count=int(r.child or 0),
                    adult_count=int(r.adult or 0),
                    unspecified_age_count=int(r.unknown_age or 0),
                    new_case_count=new_count,
                    old_case_count=old_count,
                    unspecified_case_count=max(total - new_count - old_count, 0),
                    inhouse_count=int(r.inhouse or 0),
                    outsourced_count=int(r.outsourced or 0),
                    service_type=str(r.service_type or ""),
                    opd_count=int(r.opd or 0),
                    ipd_count=int(r.ipd or 0),
                    investigation_count=int(r.investigation or 0),
                    generic_service_count=int(r.service or 0),
                )
            )
        return rows

    async def _daily_stats(self, db: AsyncSession, activity_scope):
        day_expr = func.date(activity_scope.c.activity_datetime)
        stmt = (
            select(
                day_expr.label("day"),
                func.count().label("activity_count"),
                func.count(func.distinct(activity_scope.c.patient_id)).label("unique_patients"),
                func.sum(case((activity_scope.c.activity_type == "opd", 1), else_=0)).label("opd"),
                func.sum(case((activity_scope.c.activity_type == "ipd", 1), else_=0)).label("ipd"),
                func.sum(case((activity_scope.c.activity_type == "investigation", 1), else_=0)).label("investigation"),
                func.sum(case((activity_scope.c.activity_type == "service", 1), else_=0)).label("service"),
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )
        result = await db.execute(stmt)
        return [
            DailyStatistics(
                date=r.day,
                unique_patient_count=int(r.unique_patients or 0),
                activity_count=int(r.activity_count or 0),
                opd_count=int(r.opd or 0),
                ipd_count=int(r.ipd or 0),
                investigation_count=int(r.investigation or 0),
                service_count=int(r.service or 0),
            )
            for r in result
        ]


statistics_service = StatisticsService()

__all__ = ["StatisticsService", "statistics_service"]
