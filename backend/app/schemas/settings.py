"""HHMS hospital and system settings schemas."""
from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

class HospitalRead(BaseSchema):
    id: int; hospital_name: str; hospital_code: str; address: str | None = None; city: str | None = None; state: str | None = None; pincode: str | None = None; phone: str | None = None; email: str | None = None; website: str | None = None; logo_path: str | None = None; license_no: str | None = None; registration_no: str | None = None; tax_id: str | None = None; is_active: bool; created_at: datetime; updated_at: datetime

class HospitalUpdate(BaseSchema):
    hospital_name: str = Field(min_length=1, max_length=150)
    hospital_code: str = Field(min_length=1, max_length=50)
    address: str | None = None; city: str | None = None; state: str | None = None; pincode: str | None = None; phone: str | None = None; email: str | None = None; website: str | None = None; logo_path: str | None = None; license_no: str | None = None; registration_no: str | None = None; tax_id: str | None = None; is_active: bool = True

class SystemSettingRead(BaseSchema):
    id: int; setting_key: str; setting_value: str; setting_type: str; description: str | None; is_editable: bool; created_at: datetime; updated_at: datetime

class SystemSettingUpsert(BaseSchema):
    setting_value: str = ""
    setting_type: str = Field(default="string", max_length=30)
    description: str | None = None

class NumberSequenceRead(BaseSchema):
    id: int; sequence_name: str; prefix: str; suffix: str; current_value: int; padding_length: int; reset_frequency: str; is_active: bool; created_at: datetime; updated_at: datetime

class NumberSequenceUpdate(BaseSchema):
    prefix: str = Field(default="", max_length=30)
    suffix: str = Field(default="", max_length=30)
    current_value: int = Field(default=0, ge=0)
    padding_length: int = Field(default=4, ge=1, le=12)
    reset_frequency: str = Field(default="never", max_length=20)
    is_active: bool = True

__all__ = ["HospitalRead", "HospitalUpdate", "SystemSettingRead", "SystemSettingUpsert", "NumberSequenceRead", "NumberSequenceUpdate"]
