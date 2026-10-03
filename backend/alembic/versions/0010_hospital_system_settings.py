"""Add hospital profile, system settings and number sequences."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
revision='0010_hospital_system_settings'
down_revision='0009_designation_master'
branch_labels=None
depends_on=None

def upgrade() -> None:
    op.create_table('Hospital',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hospital_name', sa.String(150), nullable=False), sa.Column('hospital_code', sa.String(50), nullable=False),
        sa.Column('address', sa.Text()), sa.Column('city', sa.String(100)), sa.Column('state', sa.String(100)), sa.Column('pincode', sa.String(20)),
        sa.Column('phone', sa.String(30)), sa.Column('email', sa.String(150)), sa.Column('website', sa.String(200)), sa.Column('logo_path', sa.String(500)),
        sa.Column('license_no', sa.String(100)), sa.Column('registration_no', sa.String(100)), sa.Column('tax_id', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('hospital_code', name='uq_hospital_code'))
    op.create_index('ix_Hospital_hospital_code','Hospital',['hospital_code'])
    op.create_table('SystemSetting',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True), sa.Column('setting_key', sa.String(120), nullable=False),
        sa.Column('setting_value', sa.Text(), nullable=False, server_default=''), sa.Column('setting_type', sa.String(30), nullable=False, server_default='string'),
        sa.Column('description', sa.Text()), sa.Column('is_editable', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('setting_key', name='uq_system_setting_key'))
    op.create_index('ix_SystemSetting_setting_key','SystemSetting',['setting_key'])
    op.create_table('NumberSequence',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True), sa.Column('sequence_name', sa.String(80), nullable=False),
        sa.Column('prefix', sa.String(30), nullable=False, server_default=''), sa.Column('suffix', sa.String(30), nullable=False, server_default=''),
        sa.Column('current_value', sa.Integer(), nullable=False, server_default='0'), sa.Column('padding_length', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('reset_frequency', sa.String(20), nullable=False, server_default='never'), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('sequence_name', name='uq_number_sequence_name'))
    op.create_index('ix_NumberSequence_sequence_name','NumberSequence',['sequence_name'])
    op.bulk_insert(sa.table('NumberSequence', sa.column('sequence_name', sa.String), sa.column('prefix', sa.String), sa.column('suffix', sa.String), sa.column('current_value', sa.Integer), sa.column('padding_length', sa.Integer), sa.column('reset_frequency', sa.String), sa.column('is_active', sa.Boolean)), [
        {'sequence_name':'patient_number','prefix':'PT','suffix':'','current_value':0,'padding_length':6,'reset_frequency':'never','is_active':True},
        {'sequence_name':'visit_number','prefix':'VIS','suffix':'','current_value':0,'padding_length':6,'reset_frequency':'daily','is_active':True},
        {'sequence_name':'admission_number','prefix':'ADM','suffix':'','current_value':0,'padding_length':6,'reset_frequency':'yearly','is_active':True},
        {'sequence_name':'invoice_number','prefix':'INV','suffix':'','current_value':0,'padding_length':6,'reset_frequency':'yearly','is_active':True},
        {'sequence_name':'opd_token','prefix':'OPD','suffix':'','current_value':0,'padding_length':3,'reset_frequency':'daily','is_active':True},
    ])

def downgrade() -> None:
    op.drop_index('ix_NumberSequence_sequence_name', table_name='NumberSequence'); op.drop_table('NumberSequence')
    op.drop_index('ix_SystemSetting_setting_key', table_name='SystemSetting'); op.drop_table('SystemSetting')
    op.drop_index('ix_Hospital_hospital_code', table_name='Hospital'); op.drop_table('Hospital')
