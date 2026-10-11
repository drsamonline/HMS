"""HHMS demo-data seeder — populates a database with a full year (2025) of data.

Creates hospital profile, staff users, departments/services/designations,
medicines + stock batches, beds, and a realistic set of patients, visits,
OPD tokens, case records, prescriptions, dispenses, investigations (+results),
IPD admissions (+progress notes, discharges), invoices and payments — all
dated inside the requested year so dashboards, statistics and print
envelopes show populated figures immediately after install.

Usage (source tree)::

    python -m app.cli.seed_demo_data [--year 2025] [--force]

The packaged server can also seed automatically at startup when
``HHMS_SEED_DEMO_DATA=true`` is set (see ``app.server.run``).

Idempotency: a marker SystemSetting row ``demo_seed.year.<YEAR>=done`` is
written after a successful run; re-running is a no-op unless ``--force``.

Exit codes: 0 success (or already seeded), 1 unexpected error.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

MIN_YEAR = 2000

# Sequence names minted by services; migration 0010 only ships the first five.
ALL_SEQUENCES = [
    ("patient_number", "PT", "", 6, "never"),
    ("visit_number", "VIS", "", 6, "daily"),
    ("admission_number", "ADM", "", 6, "yearly"),
    ("invoice_number", "INV", "", 6, "yearly"),
    ("opd_token", "OPD", "", 3, "daily"),
    ("case_number", "CASE", "", 5, "never"),
    ("prescription_number", "RX", "", 5, "daily"),
    ("receipt_number", "RCP", "", 5, "daily"),
    ("investigation_number", "LAB", "", 5, "monthly"),
    ("discharge_number", "DC", "", 5, "yearly"),
]

MEDICINES = [
    ("ARSENICUM ALB", "Arsenicum album", "mother_tincture"),
    ("NATRUM MUR", "Natrum muriaticum", "polycrest"),
    ("SULPHUR", "Sulphur", "polycrest"),
    ("PULSATILLA", "Pulsatilla nigricans", "polycrest"),
    ("CALCAREA CARB", "Calcarea carbonica", "polycrest"),
    ("LACHESIS", "Lachesis muta", "miasmatic"),
    ("LYCOPODIUM", "Lycopodium clavatum", "nosode"),
    ("NUX VOMICA", "Nux vomica", "polycrest"),
    ("SEPIA", "Sepia officinalis", "polycrest"),
    ("IGNATIA", "Ignatia amara", "acute"),
    ("APHIS MED", "Aphis mellifica", "acute"),
    ("BELLADONNA", "Belladonna", "acute"),
    ("BRYONIA", "Bryonia alba", "acute"),
    ("RUS TOX", "Rhus toxicodendron", "acute"),
    ("ARNICA", "Arnica montana", "acute"),
    ("CALEA", "Calendula officinalis", "mother_tincture"),
    ("HYPERICUM", "Hypericum perforatum", "mother_tincture"),
    ("MAG PHOS", "Magnesia phosphorica", "biochemic"),
    ("KALI MUR", "Kalium muriaticum", "biochemic"),
    ("FERRUM MET", "Ferrum metallicum", "tonic"),
    ("CHINA OFF", "China officinalis", "tonic"),
    ("IPECACUANHA", "Ipecacuanha", "acute"),
    ("ANTIM CRUD", "Antimonium crudum", "acute"),
    ("TEUCRIUM", "Teucrium marium", "liver"),
    ("CARD MAR", "Carduus marianus", "liver"),
]

POTENCIES = ["30C", "200C", "1M", "6C"]
MANUFACTURERS = ["SBL Homeopathy", "Dr. Willmar Schwabe India", "Admark Phytochem", "Hahnemann Repertory House"]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ananya", "Diya", "Saanvi", "Aadhya", "Isha", "Riya", "Myra", "Sara",
    "Imran", "Farhan", "Yusuf", "Zoya", "Ayesha", "Nida", "Rahul", "Amit",
    "Priya", "Neha", "Kavita", "Sunita", "Meena", "Rakesh", "Sanjay", "Deepa",
    "Ganesh", "Prakash", "Shweta", "Tarun", "Leela", "Naseem", "Gulshan", "Rehan",
]
LAST_NAMES = [
    "Joshi", "Patel", "Sharma", "Deshmukh", "Kulkarni", "Reddy", "Nair", "Iyer",
    "Khan", "Shaikh", "Verma", "Gupta", "Mehta", "Jain", "Bhosale", "Sawant",
    "Naik", "Pawar", "Singh", "Yadav",
]
COMPLAINTS = [
    "Recurring migraine headaches for 3 months",
    "Chronic dry cough worse at night",
    "Lower back pain radiating to left leg",
    "Recurrent acidity and bloating after meals",
    "Seasonal allergic rhinitis with sneezing",
    "Joint stiffness in both knees since winter",
    "Insomnia with difficulty falling asleep",
    "Recurring skin rash on forearms with itching",
    "Frequent throat infections over last year",
    "Mild anaemia with fatigue and breathlessness",
    "Irregular menstrual cycle with dysmenorrhoea",
    "Tension headache associated with work stress",
    "Recurrent fever with body aches every monsoon",
    "Anxiety with palpitations in crowded places",
    "Post-dengue weakness and loss of appetite",
]
DIAGNOSES = [
    "Chronic migraine without aura", "Allergic bronchitis", "Lumbar spondylosis",
    "Functional dyspepsia", "Perennial allergic rhinitis", "Osteoarthritis of knee",
    "Psychophysiological insomnia", "Atopic dermatitis", "Chronic tonsillitis",
    "Iron-deficiency anaemia", "Primary dysmenorrhoea", "Tension-type headache",
    "Recurrent viral pyrexia", "Generalised anxiety state", "Post-viral convalescence",
]
INVESTIGATION_NAMES = [
    "Complete blood count", "Liver function test", "Kidney function test",
    "Thyroid profile (TSH, T3, T4)", "Serum vitamin D", "Serum vitamin B12",
    "Blood sugar fasting + HbA1c", "Lipid profile", "Urine routine examination",
    "Chest X-ray PA view", "ECG resting", "Ultrasound abdomen whole",
]


def _parser(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="hhms seed-demo-data")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--force", action="store_true",
                        help="Seed even if this year's dataset was already created.")
    return parser.parse_args(argv)


async def _ensure_infrastructure(db) -> int:
    """Hospital row, number sequences, roles, staff users. Returns admin id."""
    from sqlalchemy import func, select

    from app.auth.password import hash_password
    from app.models.hospital import Hospital
    from app.models.number_sequence import NumberSequence
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    hospital = (await db.execute(select(Hospital).order_by(Hospital.id).limit(1))).scalar_one_or_none()
    if hospital is None:
        db.add(Hospital(
            hospital_name="Homeopathy Wellness Hospital",
            hospital_code="DEMO-HWH",
            address="12 Wellness Road, Civil Lines",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
            phone="+91 20 4000 1234",
            email="info@demo-hwh.example",
            website="https://demo-hwh.example",
            license_no="MH-HOM-DEMO-001",
            registration_no="REG-PUNE-2019-778",
            tax_id="27AAACD1234E1ZP",
        ))
        await db.flush()

    existing_seq_names = set((await db.execute(select(NumberSequence.sequence_name))).scalars().all())
    for name, prefix, suffix, pad, reset in ALL_SEQUENCES:
        if name not in existing_seq_names:
            db.add(NumberSequence(
                sequence_name=name, prefix=prefix, suffix=suffix,
                current_value=0, padding_length=pad, reset_frequency=reset,
                is_active=True,
            ))
    await db.flush()

    admin = (await db.execute(select(User).where(func.lower(User.username) == "admin"))).scalar_one_or_none()
    if admin is None:
        admin = User(
            username="admin", password_hash=hash_password("admin"),
            full_name="Hospital Administrator", email="admin@demo-hwh.example",
            designation="Administrator", is_active=True,
        )
        db.add(admin)
        await db.flush()

    role = (await db.execute(select(Role).where(func.lower(Role.role_name) == "admin"))).scalar_one_or_none()
    if role is None:
        role = Role(role_name="admin", description="System administrator", is_active=True)
        db.add(role)
        await db.flush()
    if (await db.execute(
        select(UserRole).where(UserRole.user_id == admin.id, UserRole.role_id == role.id)
    )).scalar_one_or_none() is None:
        db.add(UserRole(user_id=admin.id, role_id=role.id))
    await db.flush()

    # Demo clinicians / pharmacists / billing clerks (shared password below).
    staff_specs = [
        ("drmehta", "Dr. R. Mehta", "Consultant Physician"),
        ("drkulkarni", "Dr. P. Kulkarni", "Homoeopath"),
        ("drfaridi", "Dr. S. Faridi", "Homoeopath"),
        ("pharma1", "Pharmacy Counter 1", "Dispensing Pharmacist"),
        ("billing1", "Billing Counter 1", "Billing Clerk"),
    ]
    password_hash = hash_password("Demo@123")
    staff_ids: dict[str, int] = {"admin": admin.id}
    for username, full_name, designation in staff_specs:
        user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if user is None:
            user = User(
                username=username, password_hash=password_hash, full_name=full_name,
                email=f"{username}@demo-hwh.example", designation=designation, is_active=True,
            )
            db.add(user)
            await db.flush()
        staff_ids[username] = user.id
    await db.commit()
    return staff_ids


async def _seed_masters(db, year: int) -> dict:
    """Departments/services/designations, medicines+stock batches, beds."""
    from uuid import uuid4

    from sqlalchemy import func, select

    from app.models.bed import Bed
    from app.models.department import Department
    from app.models.department_service import DepartmentService
    from app.models.designation import Designation
    from app.models.medicine import Medicine
    from app.models.stock_batch import StockBatch
    from app.schemas.bed import BedCreate
    from app.schemas.department import DepartmentCreate
    from app.schemas.department_service import DepartmentServiceCreate
    from app.schemas.designation import DesignationCreate
    from app.schemas.medicine import MedicineCreate
    from app.schemas.stock_batch import StockBatchCreate
    from app.services.bed import bed_service
    from app.services.department import department_service
    from app.services.department_service import department_service_manager
    from app.services.designation import designation_service
    from app.services.medicine import medicine_service
    from app.services.stock_batch import stock_batch_service

    async def _exists(model, column, value) -> bool:
        return (await db.execute(
            select(func.count()).select_from(model).where(column == value)
        )).scalar_one() > 0

    ids: dict = {}

    departments = [
        ("OPD", "Outpatient Department", "clinical"),
        ("IPD", "Inpatient Department", "clinical"),
        ("PHARMACY", "Pharmacy", "support"),
        ("LAB", "Laboratory", "diagnostic"),
        ("BILLING", "Billing & Accounts", "financial"),
    ]
    dept_ids = {}
    for code, name, dtype in departments:
        if not await _exists(Department, Department.code, code):
            await department_service.create(db, DepartmentCreate(
                code=code, name=name, description=f"Demo {name}", department_type=dtype,
            ))
        row = (await db.execute(
            select(Department.id).where(Department.code == code)
        )).scalars().first()
        dept_ids[code] = row
    ids["departments"] = dept_ids

    service_map = {
        "OPD": [("GEN", "General Consultation"), ("PED", "Paediatrics"), ("DERM", "Dermatology")],
        "IPD": [("GEN-WARD", "General Ward"), ("DAYCARE", "Day Care")],
        "LAB": [("PATH", "Pathology"), ("RADIO", "Radiology")],
    }
    svc_ids = {}
    for dept_code, services in service_map.items():
        for scode, sname in services:
            existing = (await db.execute(
                select(DepartmentService.id).where(
                    DepartmentService.code == scode,
                    DepartmentService.department_id == dept_ids[dept_code],
                )
            )).scalars().first()
            if existing is None:
                svc = await department_service_manager.create(db, DepartmentServiceCreate(
                    department_id=dept_ids[dept_code], parent_service_id=None,
                    code=scode, name=sname, description=f"Demo service {sname}",
                ))
                existing = svc.id
            svc_ids[f"{dept_code}:{scode}"] = existing
    ids["services"] = svc_ids

    for code, name, dtype in [
        ("CONSULT", "Consultant", "medical"),
        ("RESIDENT", "Resident Doctor", "medical"),
        ("PHARM", "Pharmacist", "paramedical"),
        ("CLERK", "Billing Clerk", "administrative"),
        ("HEADNURSE", "Head Nurse", "nursing"),
    ]:
        if not await _exists(Designation, Designation.code, code):
            await designation_service.create(db, DesignationCreate(
                code=code, name=name, description=f"Demo designation {name}", designation_type=dtype,
            ))

    medicines = []
    for code, sci_name, mtype in MEDICINES:
        med_code = f"{code}-{year}"
        if not await _exists(Medicine, Medicine.medicine_code, med_code):
            med = await medicine_service.create(db, MedicineCreate(
                medicine_code=med_code, medicine_name=code.title(),
                scientific_name=sci_name, medicine_type=mtype,
                description=f"Demo master entry for {code.title()}",
            ))
        else:
            med = (await db.execute(
                select(Medicine).where(Medicine.medicine_code == med_code)
            )).scalar_one()
        medicines.append(med)
    ids["medicines"] = medicines

    rng = random.Random(year * 7 + 11)
    existing_batch_meds = set((await db.execute(
        select(StockBatch.medicine_id)
    )).scalars().all())
    stock_batches = list((await db.execute(
        select(StockBatch).where(StockBatch.medicine_id.in_({m.id for m in medicines}))
    )).scalars().all()) if existing_batch_meds else []
    for med in medicines:
        if med.id in existing_batch_meds:
            continue
        for potency in rng.sample(POTENCIES, k=rng.randint(1, 2)):
            mfg = date(year, rng.randint(1, 6), rng.randint(1, 28))
            expiry = date(year + 2, rng.randint(1, 12), rng.randint(1, 28))
            batch = await stock_batch_service.create(db, StockBatchCreate(
                medicine_id=med.id,
                batch_no=f"B{uuid4().hex[:8].upper()}",
                manufacture_date=mfg,
                expiry_date=expiry,
                quantity_received=Decimal(rng.choice([50, 100, 150, 200])),
                unit_cost=Decimal(rng.randint(40, 300)),
            ))
            stock_batches.append(batch)
    ids["stock_batches"] = stock_batches

    beds = list((await db.execute(select(Bed))).scalars().all())
    if not beds:
        wards = [("General Ward A", 8), ("General Ward B", 8), ("Day Care", 4)]
        ward_no = 1
        for ward, count in wards:
            for n in range(1, count + 1):
                bed = await bed_service.create(db, BedCreate(
                    bed_number=f"W{ward_no}-B{n}", ward=ward,
                    room_number=f"R{ward_no}", bed_type="standard",
                ))
                beds.append(bed)
            ward_no += 1
    ids["beds"] = beds
    return ids


async def _seed_transactions(db, year: int, staff: dict, masters: dict) -> dict:
    from sqlalchemy import select

    from app.schemas.admission import AdmissionCreate
    from app.schemas.billing import InvoiceCreate, InvoiceItemCreate, PaymentCreate
    from app.schemas.case_record import CaseRecordCreate
    from app.schemas.discharge import DischargeCreate
    from app.schemas.dispense import DispenseCreate
    from app.schemas.investigation import InvestigationCreate
    from app.schemas.investigation_result import InvestigationResultCreate
    from app.schemas.opd_token import OPDTokenCreate
    from app.schemas.patient import PatientCreate
    from app.schemas.prescription import PrescriptionCreate, PrescriptionItemCreate
    from app.schemas.progress_note import ProgressNoteCreate
    from app.schemas.visit import VisitCreate
    from app.services.admission import admission_service
    from app.services.billing import billing_service
    from app.services.case_record import case_record_service
    from app.services.discharge import discharge_service
    from app.services.dispense import dispense_service
    from app.services.investigation import investigation_service
    from app.services.investigation_result import investigation_result_service
    from app.services.opd_token import opd_token_service
    from app.services.patient import patient_service
    from app.services.prescription import prescription_service
    from app.services.progress_note import progressNote_service
    from app.services.visit import visit_service

    rng = random.Random(year * 13 + 3)
    doctors = [staff["drmehta"], staff["drkulkarni"], staff["drfaridi"]]
    pharmacist = staff["pharma1"]
    biller = staff["billing1"]
    medicines = masters["medicines"]
    stock_batches = masters["stock_batches"]
    beds = list(masters["beds"])
    dept_ids = masters["departments"]
    svc_ids = masters["services"]

    counters = {"patients": 0, "visits": 0, "prescriptions": 0, "dispenses": 0,
                "investigations": 0, "admissions": 0, "invoices": 0, "payments": 0}

    def dt(day: date, hour: int, minute: int) -> datetime:
        return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)

    def visit_day(i: int) -> date:
        start = date(year, 1, 6)  # a Monday
        week = i // 5
        weekday = i % 5
        return start + timedelta(weeks=week, days=weekday)

    # ---- Patients -----------------------------------------------------
    patients = []
    for i in range(40):
        dob_year = year - rng.randint(6, 78)
        p = await patient_service.create(db, patient_in=PatientCreate(
            first_name=rng.choice(FIRST_NAMES),
            last_name=rng.choice(LAST_NAMES),
            gender=rng.choice(["Male", "Female"]),
            date_of_birth=date(dob_year, rng.randint(1, 12), rng.randint(1, 28)),
            age=year - dob_year,
            blood_group=rng.choice(["A+", "B+", "O+", "AB+", "A-", "O-"]),
            mobile_number=f"+91 9{rng.randint(100000000, 999999999)}",
            city=rng.choice(["Pune", "Nashik", "Satara", "Solapur", "Mumbai"]),
            state="Maharashtra",
            occupation=rng.choice(["Teacher", "Engineer", "Student", "Homemaker",
                                   "Business", "Retired", "Nurse", "Driver"]),
            marital_status=rng.choice(["Single", "Married"]),
        ))
        patients.append(p)
        counters["patients"] += 1

    # ---- OPD visits with token, case, prescription, dispense, invoice --
    for i in range(120):
        patient = patients[i % len(patients)]
        day = visit_day(i)
        doctor = doctors[i % len(doctors)]
        complaint = COMPLAINTS[i % len(COMPLAINTS)]
        visit_time = dt(day, 9 + (i % 8), (i * 7) % 60)

        visit = await visit_service.create(db, visit_in=VisitCreate(
            patient_id=patient.id,
            visit_type="new" if i % 3 == 0 else "follow_up",
            visit_datetime=visit_time,
            chief_complaint=complaint,
            consultation_status="completed",
            consulting_doctor_id=doctor,
            department_id=dept_ids["OPD"],
            service_id=svc_ids["OPD:GEN"],
            case_type="new" if i % 3 == 0 else "old",
        ))
        counters["visits"] += 1

        await opd_token_service.create(db, token_in=OPDTokenCreate(
            visit_id=visit.id, queue_date=day,
        ))

        await case_record_service.create(db, CaseRecordCreate(
            patient_id=patient.id, visit_id=visit.id, case_status="active",
            chief_complaints=complaint,
            history_present_illness=f"{complaint}. Gradual onset, worse in the morning.",
            clinical_examination="Vitals stable. Systemic examination unremarkable.",
            totality="Thirsty, warm patient; aggravated by heat and exertion.",
        ), created_by=doctor)

        rx_items = []
        chosen = rng.sample(medicines, k=rng.randint(1, 3))
        for med in chosen:
            rx_items.append(PrescriptionItemCreate(
                medicine_id=med.id,
                dosage="2 drops / 2 pills",
                frequency=rng.choice(["TDS", "BD", "QDS", "OD"]),
                duration_days=rng.choice([5, 7, 10, 14]),
                instructions="After meals, half an hour before food",
                quantity=Decimal(rng.choice([1, 2, 3])),
            ))
        prescription = await prescription_service.create(db, PrescriptionCreate(
            visit_id=visit.id,
            prescribed_by=doctor,
            prescription_datetime=visit_time + timedelta(minutes=20),
            diagnosis=DIAGNOSES[i % len(DIAGNOSES)],
            clinical_notes="Case taking completed; remedy matched to symptom totality.",
            treatment_plan="Constitutional prescribing with monthly follow-up.",
            items=rx_items,
        ))
        counters["prescriptions"] += 1

        # The Prescription model has no ORM relationship to its items;
        # fetch them by foreign key and pair each with its medicine master.
        from app.models.prescription_item import PrescriptionItem

        item_models = list((await db.execute(
            select(PrescriptionItem).where(
                PrescriptionItem.prescription_id == prescription.id
            ).order_by(PrescriptionItem.id)
        )).scalars().all())
        med_by_id = {med.id: med for med in chosen}
        item_rows = [(item, med_by_id[item.medicine_id])
                     for item in item_models if item.medicine_id in med_by_id]
        amount = Decimal("0")
        for item, med in item_rows:
            candidates = [b for b in stock_batches if b.medicine_id == med.id]
            if not candidates:
                continue
            batch = max(candidates, key=lambda b: b.quantity_remaining)
            if batch.quantity_remaining < item.quantity:
                continue
            try:
                await dispense_service.create(db, DispenseCreate(
                    prescription_item_id=item.id,
                    medicine_id=med.id,
                    stock_batch_id=batch.id,
                    quantity_dispensed=item.quantity,
                    dispensed_by=pharmacist,
                ), performed_by=pharmacist)
                counters["dispenses"] += 1
                await db.refresh(batch)
            except Exception:  # noqa: BLE001 - never abort the whole seed for one line
                continue
            amount += item.quantity * Decimal(60)

        consult_fee = Decimal(rng.choice([300, 400, 500]))
        total = consult_fee + amount
        invoice = await billing_service.create_invoice(db, InvoiceCreate(
            patient_id=patient.id, visit_id=visit.id,
            invoice_date=visit_time + timedelta(minutes=45),
            total_amount=total,
            remarks="OPD consultation + dispensing",
        ), generated_by=biller)
        counters["invoices"] += 1
        await billing_service.add_invoice_item(db, invoice.id, InvoiceItemCreate(
            item_type="consultation", description="OPD consultation fee",
            quantity=Decimal(1), unit_price=consult_fee,
        ))
        await billing_service.add_invoice_item(db, invoice.id, InvoiceItemCreate(
            item_type="medicine", description="Dispensed homoeopathic medicines",
            quantity=Decimal(1), unit_price=amount or Decimal("0"),
        ))

        roll = rng.random()
        pay_time = visit_time + timedelta(minutes=50)
        if roll < 0.70:
            await billing_service.create_payment(db, PaymentCreate(
                invoice_id=invoice.id, payment_datetime=pay_time,
                payment_method=rng.choice(["cash", "upi", "card"]),
                amount_paid=total, transaction_reference=f"TXN{rng.randint(100000, 999999)}",
            ), received_by=biller)
            counters["payments"] += 1
        elif roll < 0.90:
            await billing_service.create_payment(db, PaymentCreate(
                invoice_id=invoice.id, payment_datetime=pay_time,
                payment_method="cash", amount_paid=(total / 2).quantize(Decimal("0.01")),
            ), received_by=biller)
            counters["payments"] += 1

        # Investigations attached to roughly every third visit.
        if i % 3 == 0:
            inv = await investigation_service.create(db, InvestigationCreate(
                patient_id=patient.id, visit_id=visit.id,
                department_id=dept_ids["LAB"], service_id=svc_ids["LAB:PATH"],
                case_type="new" if i % 3 == 0 else "old",
                fulfillment_mode="in_house",
                investigation_name=INVESTIGATION_NAMES[i % len(INVESTIGATION_NAMES)],
                requested_by=doctor,
                requested_datetime=visit_time + timedelta(minutes=10),
                investigation_status="completed",
            ))
            counters["investigations"] += 1
            result_day = min(day + timedelta(days=rng.randint(1, 4)), date(year, 12, 31))
            await investigation_result_service.create(db, InvestigationResultCreate(
                investigation_id=inv.id,
                result_text="Values within normal limits; mild deficiency noted where applicable.",
                interpretation="Correlate clinically; supplementation advised.",
                result_datetime=dt(result_day, 15, 30),
                verified_by=doctor,
                verification_datetime=dt(result_day, 16, 0),
                report_status="verified",
            ))

    # ---- IPD admissions ----------------------------------------------
    for j in range(8):
        patient = patients[(j * 5 + 3) % len(patients)]
        admit_day = date(year, 2 + j, 10 + j)
        if admit_day.year != year:
            admit_day = date(year, 12, 10)
        doctor = doctors[j % len(doctors)]
        bed = beds[j]
        admission = await admission_service.create(db, admission_in=AdmissionCreate(
            patient_id=patient.id,
            admission_datetime=dt(admit_day, 11, 0),
            bed_id=bed.id,
            admitted_by=doctor,
            department_id=dept_ids["IPD"],
            service_id=svc_ids["IPD:GEN-WARD"],
            case_type="old",
            admission_reason=COMPLAINTS[(j * 3) % len(COMPLAINTS)],
        ))
        counters["admissions"] += 1

        stay = rng.randint(2, 5)
        for d in range(stay):
            note_day = min(admit_day + timedelta(days=d + 1), date(year, 12, 31))
            await progressNote_service.create(db, ProgressNoteCreate(
                admission_id=admission.id,
                note_datetime=dt(note_day, 10, 0),
                subjective="Patient reports gradual improvement; sleeping well.",
                objective="Afebrile, vitals stable, general condition improving.",
                assessment="Responding to constitutional therapy.",
                plan="Continue current management; plan discharge if stable.",
                recorded_by=doctor,
            ))

        discharge_day = min(admit_day + timedelta(days=stay), date(year, 12, 31))
        await discharge_service.create(db, data=DischargeCreate(
            admission_id=admission.id,
            discharge_datetime=dt(discharge_day, 14, 0),
            discharge_summary="Improved; discharged with oral advice and follow-up in 4 weeks.",
            discharge_status="discharged",
            discharged_by=doctor,
        ))

        ipd_total = Decimal(1200 * stay)
        invoice = await billing_service.create_invoice(db, InvoiceCreate(
            patient_id=patient.id, admission_id=admission.id,
            invoice_date=dt(discharge_day, 15, 0),
            total_amount=ipd_total,
            remarks=f"IPD charges ({stay} days)",
        ), generated_by=biller)
        counters["invoices"] += 1
        await billing_service.add_invoice_item(db, invoice.id, InvoiceItemCreate(
            item_type="room", description=f"Bed charges x {stay} days",
            quantity=Decimal(stay), unit_price=Decimal(1200),
        ))
        if j < 6:
            await billing_service.create_payment(db, PaymentCreate(
                invoice_id=invoice.id, payment_datetime=dt(discharge_day, 15, 30),
                payment_method=rng.choice(["cash", "upi", "bank_transfer"]),
                amount_paid=ipd_total, transaction_reference=f"IPD{rng.randint(100000, 999999)}",
            ), received_by=biller)
            counters["payments"] += 1
        elif j == 6:
            await billing_service.create_payment(db, PaymentCreate(
                invoice_id=invoice.id, payment_datetime=dt(discharge_day, 15, 30),
                payment_method="cheque", amount_paid=(ipd_total / 2).quantize(Decimal("0.01")),
            ), received_by=biller)
            counters["payments"] += 1
        # j == 7 stays unpaid (shows outstanding balance on dashboards)

    # One refund scenario on a fully-paid early invoice.
    paid_invoices_sample = None
    from sqlalchemy import select as sa_select
    from app.models.invoice import Invoice
    paid_invoices_sample = (await db.execute(
        sa_select(Invoice).where(Invoice.payment_status == "paid").order_by(Invoice.id).limit(1)
    )).scalar_one_or_none()
    if paid_invoices_sample is not None:
        await billing_service.create_payment(db, PaymentCreate(
            invoice_id=paid_invoices_sample.id,
            payment_datetime=dt(date(year, 12, 28), 12, 0),
            payment_method="cash",
            amount_paid=Decimal("-100"),
            remarks="Goodwill refund - cancelled lab add-on",
        ), received_by=biller)
        counters["payments"] += 1

    return counters


async def _seed(year: int, force: bool) -> int:
    from sqlalchemy import func, select

    # Ensure schema exists (Alembic migrations) before touching any table so
    # the CLI works on a fresh install without first booting the server.
    from app.startup import prepare_runtime

    prepare_runtime()

    from app.db.session import get_session_factory
    from app.models.system_setting import SystemSetting
    from app.models.user import User

    factory = get_session_factory()
    marker_key = f"demo_seed.year.{year}"

    async with factory() as db:
        # Safety gate: demo data must never be injected into a live hospital
        # database that already has real patients.  Seeding proceeds only on
        # an empty database or one previously seeded by this CLI (marker set).
        marker = (await db.execute(
            select(SystemSetting).where(SystemSetting.setting_key == marker_key)
        )).scalar_one_or_none()
        from app.models.patient import Patient

        patient_count = (await db.execute(
            select(func.count()).select_from(Patient)
        )).scalar_one()
        if patient_count > 0 and marker is None and not force:
            print(
                f"Refusing to seed: database already contains {patient_count} "
                f"real patient record(s) and no '{marker_key}' marker. "
                "Use --force to override."
            )
            return 2
        if marker is not None and not force:
            print(f"Demo data for {year} already seeded ({marker_key}); use --force to re-seed.")
            return 0

        staff = await _ensure_infrastructure(db)
        masters = await _seed_masters(db, year)
        counters = await _seed_transactions(db, year, staff, masters)

        if marker is None:
            db.add(SystemSetting(
                setting_key=marker_key, setting_value="done", setting_type="string",
                description=f"Demo dataset for {year} seeded by app.cli.seed_demo_data.",
                is_editable=False,
            ))
            await db.commit()

    print(
        f"Seeded {year} demo data: {counters['patients']} patients, "
        f"{counters['visits']} visits, {counters['prescriptions']} prescriptions, "
        f"{counters['dispenses']} dispenses, {counters['investigations']} investigations, "
        f"{counters['admissions']} admissions, {counters['invoices']} invoices, "
        f"{counters['payments']} payments."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser(argv)
    if not (MIN_YEAR <= args.year <= 2100):
        print(f"error: --year must be between {MIN_YEAR} and 2100", file=sys.stderr)
        return 1
    try:
        return asyncio.run(_seed(args.year, args.force))
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"error: demo seeding failed: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def maybe_seed_from_env() -> None:
    """Startup hook: seed demo data when HHMS_SEED_DEMO_DATA is truthy."""
    flag = os.environ.get("HHMS_SEED_DEMO_DATA", "").strip().lower()
    if flag not in {"true", "1", "yes"}:
        return
    year = int(os.environ.get("HHMS_SEED_DEMO_YEAR", "2025"))
    main(["--year", str(year)])


if __name__ == "__main__":
    raise SystemExit(main())
