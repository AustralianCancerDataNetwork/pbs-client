import sqlalchemy as sa

from pbs_client.db import MODEL_BY_NAME, RESOURCE_SPECS, SYNC_ORDER


def test_all_api_resources_have_models_and_keys():
    assert len(RESOURCE_SPECS) == 35
    assert set(SYNC_ORDER) == set(MODEL_BY_NAME)
    assert all(spec.primary_key for spec in RESOURCE_SPECS)
    assert all(set(spec.primary_key) <= set(spec.fields) for spec in RESOURCE_SPECS)


def test_identifier_columns_use_integral_types():
    identifier_names = {
        "schedule_code",
        "container_code",
        "organisation_id",
        "criteria_prescribing_txt_id",
        "parameter_prescribing_txt_id",
        "indication_prescribing_txt_id",
        "prescribing_txt_id",
        "prescribing_text_id",
        "pbs_concept_id",
        "source_schedule_code",
        "target_revision_number",
        "source_revision_number",
    }

    for model in MODEL_BY_NAME.values():
        for column in model.__table__.columns:
            if column.name in identifier_names:
                assert isinstance(column.type, sa.Integer), (model.__name__, column.name)
