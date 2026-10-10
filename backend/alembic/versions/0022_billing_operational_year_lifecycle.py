"""Billing annual lifecycle: Invoice/Payment lifecycle columns and archive references.

Batch 71 - Billing Annual Lifecycle & Rollover.

Adds operational-year lifecycle columns to Invoice (invoice_year, storage_tier,
is_current_year) and Payment (payment_year, storage_tier, is_current_year),
backfills the year fields from the calendar year of the business timestamps,
and creates the permanent live-database InvoiceArchiveReference and
PaymentArchiveReference tables so billing identity survives physical annual
rollover.
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_billing_operational_year_lifecycle"
down_revision = "0021_visit_operational_year_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "Invoice",
        sa.Column("invoice_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "Invoice",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "Invoice",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_index("ix_invoice_invoice_year", "Invoice", ["invoice_year"])
    op.create_index("ix_invoice_storage_tier", "Invoice", ["storage_tier"])
    op.create_index("ix_invoice_is_current_year", "Invoice", ["is_current_year"])

    # Backfill invoice_year from the calendar year of invoice_date.
    op.execute(
        "UPDATE Invoice SET invoice_year = CAST(strftime('%Y', invoice_date) AS INTEGER)"
        " WHERE invoice_date IS NOT NULL"
    )

    op.add_column(
        "Payment",
        sa.Column("payment_year", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "Payment",
        sa.Column(
            "storage_tier",
            sa.String(20),
            nullable=False,
            server_default="live",
        ),
    )
    op.add_column(
        "Payment",
        sa.Column(
            "is_current_year",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    # Payments may outlive their rolled-over invoice; the link becomes
    # detachable during annual billing rollover.
    with op.batch_alter_table("Payment") as batch_op:
        batch_op.alter_column(
            "invoice_id", existing_type=sa.Integer(), nullable=True
        )
    op.create_index("ix_payment_payment_year", "Payment", ["payment_year"])
    op.create_index("ix_payment_storage_tier", "Payment", ["storage_tier"])
    op.create_index("ix_payment_is_current_year", "Payment", ["is_current_year"])

    # Backfill payment_year from the calendar year of payment_datetime.
    op.execute(
        "UPDATE Payment SET payment_year = CAST(strftime('%Y', payment_datetime) AS INTEGER)"
        " WHERE payment_datetime IS NOT NULL"
    )

    op.create_table(
        "InvoiceArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_invoice_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(20), nullable=False),
        sa.Column("invoice_year", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_status", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_invoice_archive_ref_manifest",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_invoice_archive_ref_patient",
        ),
        sa.UniqueConstraint(
            "original_invoice_id",
            name="uq_invoice_archive_ref_original_invoice",
        ),
    )
    op.create_index(
        "ix_invoice_archive_reference_manifest",
        "InvoiceArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_invoice_archive_reference_original_invoice",
        "InvoiceArchiveReference",
        ["original_invoice_id"],
    )
    op.create_index(
        "ix_invoice_archive_reference_patient",
        "InvoiceArchiveReference",
        ["patient_id"],
    )
    op.create_index(
        "ix_invoice_archive_reference_invoice_number",
        "InvoiceArchiveReference",
        ["invoice_number"],
    )
    op.create_index(
        "ix_invoice_archive_reference_year",
        "InvoiceArchiveReference",
        ["invoice_year"],
    )

    op.create_table(
        "PaymentArchiveReference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("archive_manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_payment_id", sa.Integer(), nullable=False),
        sa.Column("original_invoice_id", sa.Integer(), nullable=False),
        sa.Column("receipt_number", sa.String(20), nullable=False),
        sa.Column("payment_year", sa.Integer(), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["archive_manifest_id"],
            ["ArchiveManifest.id"],
            name="fk_payment_archive_ref_manifest",
        ),
        sa.UniqueConstraint(
            "original_payment_id",
            name="uq_payment_archive_ref_original_payment",
        ),
    )
    op.create_index(
        "ix_payment_archive_reference_manifest",
        "PaymentArchiveReference",
        ["archive_manifest_id"],
    )
    op.create_index(
        "ix_payment_archive_reference_original_payment",
        "PaymentArchiveReference",
        ["original_payment_id"],
    )
    op.create_index(
        "ix_payment_archive_reference_original_invoice",
        "PaymentArchiveReference",
        ["original_invoice_id"],
    )
    op.create_index(
        "ix_payment_archive_reference_receipt_number",
        "PaymentArchiveReference",
        ["receipt_number"],
    )
    op.create_index(
        "ix_payment_archive_reference_year",
        "PaymentArchiveReference",
        ["payment_year"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_archive_reference_year", table_name="PaymentArchiveReference"
    )
    op.drop_index(
        "ix_payment_archive_reference_receipt_number",
        table_name="PaymentArchiveReference",
    )
    op.drop_index(
        "ix_payment_archive_reference_original_invoice",
        table_name="PaymentArchiveReference",
    )
    op.drop_index(
        "ix_payment_archive_reference_original_payment",
        table_name="PaymentArchiveReference",
    )
    op.drop_index(
        "ix_payment_archive_reference_manifest", table_name="PaymentArchiveReference"
    )
    op.drop_table("PaymentArchiveReference")

    op.drop_index(
        "ix_invoice_archive_reference_year", table_name="InvoiceArchiveReference"
    )
    op.drop_index(
        "ix_invoice_archive_reference_invoice_number",
        table_name="InvoiceArchiveReference",
    )
    op.drop_index(
        "ix_invoice_archive_reference_patient", table_name="InvoiceArchiveReference"
    )
    op.drop_index(
        "ix_invoice_archive_reference_original_invoice",
        table_name="InvoiceArchiveReference",
    )
    op.drop_index(
        "ix_invoice_archive_reference_manifest", table_name="InvoiceArchiveReference"
    )
    op.drop_table("InvoiceArchiveReference")

    op.drop_index("ix_payment_is_current_year", table_name="Payment")
    op.drop_index("ix_payment_storage_tier", table_name="Payment")
    op.drop_index("ix_payment_payment_year", table_name="Payment")
    with op.batch_alter_table("Payment") as batch_op:
        batch_op.alter_column(
            "invoice_id", existing_type=sa.Integer(), nullable=False
        )
    op.drop_column("Payment", "is_current_year")
    op.drop_column("Payment", "storage_tier")
    op.drop_column("Payment", "payment_year")

    op.drop_index("ix_invoice_is_current_year", table_name="Invoice")
    op.drop_index("ix_invoice_storage_tier", table_name="Invoice")
    op.drop_index("ix_invoice_invoice_year", table_name="Invoice")
    op.drop_column("Invoice", "is_current_year")
    op.drop_column("Invoice", "storage_tier")
    op.drop_column("Invoice", "invoice_year")
