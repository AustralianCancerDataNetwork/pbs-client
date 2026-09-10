import sqlalchemy as sa

from pbs_client.db import MODEL_BY_NAME, RESOURCE_SPECS, SYNC_ORDER


def test_all_api_resources_have_models_and_keys():
    assert len(RESOURCE_SPECS) == 35
    # ItemOverview is opt-in only (see schema.py): it duplicates Item plus 8
    # already-synced relationship tables
    assert set(MODEL_BY_NAME) - set(SYNC_ORDER) == {"ItemOverview"}
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


def test_resource_references_use_schedule_scoped_foreign_keys():
    expected = {
        "ATC": {("schedule_code", "atc_parent_code", "pbs_atc")},
        "ContainerWholesalerRltd": {
            ("schedule_code", "container_code", "pbs_container"),
            ("schedule_code", "organisation_id", "pbs_organisation"),
        },
        "Criteria": {("schedule_code", "criteria_prescribing_txt_id", "pbs_prescribingtxt")},
        "CriteriaParameterRltd": {
            ("schedule_code", "criteria_prescribing_txt_id", "pbs_criteria"),
            ("schedule_code", "parameter_prescribing_txt_id", "pbs_prescribingtxt"),
        },
        "ExPrepSfpRltd": {
            ("schedule_code", "sfp_pbs_code", "pbs_standardformulapreparations"),
            ("schedule_code", "ex_prep_pbs_code", "pbs_extemporaneouspreparation"),
        },
        "Fee": {("schedule_code", "program_code", "pbs_program")},
        "Indication": {("schedule_code", "indication_prescribing_txt_id", "pbs_prescribingtxt")},
        "Item": {
            ("schedule_code", "program_code", "pbs_program"),
            ("schedule_code", "organisation_id", "pbs_organisation"),
        },
        "ItemAmt": {("schedule_code", "li_item_id", "pbs_item")},
        "ItemAtcRltd": {
            ("schedule_code", "atc_code", "pbs_atc"),
        },
        "ItemDispensingRuleRltd": {
            ("schedule_code", "li_item_id", "pbs_item"),
            ("schedule_code", "dispensing_rule_mnem", "pbs_dispensingrule"),
        },
        "ItemOrganisationRltd": {
            ("schedule_code", "organisation_id", "pbs_organisation"),
        },
        "ItemPrescribingTxtRltd": {
            ("schedule_code", "prescribing_txt_id", "pbs_prescribingtxt"),
        },
        "ItemPricingEvent": {("schedule_code", "li_item_id", "pbs_item")},
        "ItemRestrictionRltd": {
            ("schedule_code", "res_code", "pbs_restrictiontext"),
        },
        "MarkupBand": {
            ("schedule_code", "program_code", "pbs_program"),
            ("schedule_code", "dispensing_rule_mnem", "pbs_dispensingrule"),
        },
        "Parameter": {("schedule_code", "parameter_prescribing_txt_id", "pbs_prescribingtxt")},
        "ProgramDispensingRules": {
            ("schedule_code", "program_code", "pbs_program"),
            ("schedule_code", "dispensing_rule_mnem", "pbs_dispensingrule"),
        },
        "RstrctnPrscrbngTxtRltd": {
            ("schedule_code", "res_code", "pbs_restrictiontext"),
            ("schedule_code", "prescribing_text_id", "pbs_prescribingtxt"),
        },
    }
    for model_name, references in expected.items():
        model = MODEL_BY_NAME[model_name]
        actual = {
            (
                tuple(element.parent.name for element in constraint.elements),
                constraint.elements[0].target_fullname.split(".")[0],
            )
            for constraint in model.__table__.foreign_key_constraints
            if constraint.elements[0].target_fullname.split(".")[0] != "pbs_schedule"
        }
        assert {
            (columns, table)
            for columns, table in actual
            if columns in {reference[:2] for reference in references}
        } == {(reference[:2], reference[2]) for reference in references}

    summary = MODEL_BY_NAME["SummaryOfChanges"]
    assert {
        (
            tuple(element.parent.name for element in constraint.elements),
            constraint.elements[0].target_fullname.split(".")[0],
        )
        for constraint in summary.__table__.foreign_key_constraints
    } >= {(("source_schedule_code",), "pbs_schedule")}

    for model in MODEL_BY_NAME.values():
        if model.__name__ != "Schedule" and "schedule_code" in model.__table__.columns:
            assert any(
                tuple(element.parent.name for element in constraint.elements) == ("schedule_code",)
                and constraint.elements[0].target_fullname == "pbs_schedule.schedule_code"
                for constraint in model.__table__.foreign_key_constraints
            ), model.__name__
