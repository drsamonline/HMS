def test_ipd_clinical_imports():
    from app.models.ipd_assessment import IPDAssessment
    from app.models.pain_assessment import PainAssessment
    from app.models.nutritional_assessment import NutritionalAssessment
    from app.models.diet_chart import DietChart
    from app.models.progress_note import ProgressNote
    assert all([IPDAssessment, PainAssessment, NutritionalAssessment, DietChart, ProgressNote])
