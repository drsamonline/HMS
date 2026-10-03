"""Regression tests for hospital/system settings client contract."""
from app.schemas.settings import HospitalUpdate, NumberSequenceUpdate, SystemSettingUpsert

def test_settings_schemas_accept_core_fields():
    hospital=HospitalUpdate(hospital_name='HHMS',hospital_code='HHMS-001')
    assert hospital.hospital_name=='HHMS'
    seq=NumberSequenceUpdate(current_value=10,padding_length=6)
    assert seq.current_value==10 and seq.padding_length==6
    setting=SystemSettingUpsert(setting_value='enabled',setting_type='string')
    assert setting.setting_value=='enabled'
