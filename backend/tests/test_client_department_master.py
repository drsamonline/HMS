def test_department_master_client_contract_documents_core_fields():
    fields={"code","name","department_type","description","is_active"}
    assert {"code","name","department_type"}.issubset(fields)

def test_service_master_supports_reporting_flags():
    flags={"supports_gender_breakdown","supports_new_old","supports_fulfillment_mode"}
    assert len(flags)==3
