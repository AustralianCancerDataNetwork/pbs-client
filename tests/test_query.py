from __future__ import annotations

from pbs_client.db.model import (
    ATC,
    Copayment,
    Criteria,
    CriteriaParameterRltd,
    DispensingRule,
    Fee,
    Indication,
    Item,
    ItemAmt,
    ItemAtcRltd,
    ItemDispensingRuleRltd,
    ItemOrganisationRltd,
    ItemPrescribingTxtRltd,
    ItemPricingEvent,
    ItemRestrictionRltd,
    MarkupBand,
    Organisation,
    Parameter,
    PrescribingTxt,
    Program,
    RestrictionText,
    RstrctnPrscrbngTxtRltd,
    Schedule,
)
from pbs_client.toolkit.analytics import get_item_criteria_breakdown, indication_candidates
from pbs_client.toolkit.core import (
    BenefitTypeCode,
    MpComponentSplit,
    expand_item,
    find_items,
    get_item_amt_hierarchy,
    get_item_dispensing_rule_links,
    get_item_indication_text,
    get_item_manufacturer,
    resolve_schedule,
    split_mp_components,
)
from pbs_client.toolkit.pricing import get_item_pricing_breakdown


def test_offline_item_restriction_and_atc_expansion(session_factory):
    with session_factory() as session:
        session.add(
            Schedule(
                schedule_code=7,
                effective_date="2026-01-01",
                effective_year=2026,
                revision_number=1,
                start_tsp="2026-01-01T00:00:00Z",
                effective_month="January",
                publication_status="PUBLISHED",
            )
        )
        session.commit()
        session.add_all(
            [
                Item(schedule_code=7, li_item_id="li-1", pbs_code="X1", drug_name="Drug"),
                ATC(schedule_code=7, atc_code="A01", atc_description="Example", atc_level=1),
                RestrictionText(
                    schedule_code=7,
                    res_code="R1",
                    schedule_html_text="Use for indication",
                    note_indicator="N",
                    caution_indicator="N",
                    complex_authority_rqrd_ind="N",
                    variation_rule_applied="N",
                    first_listing_date="2026-01-01",
                    written_authority_required="N",
                ),
                PrescribingTxt(
                    schedule_code=7,
                    prescribing_txt_id=9,
                    prescribing_type="INDICATION",
                    prescribing_txt="Text",
                    prscrbg_txt_html="<p>Text</p>",
                    complex_authority_rqrd_ind="N",
                    apply_to_increase_mq_flag="N",
                    apply_to_increase_nr_flag="N",
                ),
            ]
        )
        session.commit()
        session.add_all(
            [
                ItemAtcRltd(schedule_code=7, pbs_code="X1", atc_code="A01", atc_priority_pct=100),
                ItemRestrictionRltd(
                    schedule_code=7,
                    pbs_code="X1",
                    res_code="R1",
                    benefit_type_code="R",
                    restriction_indicator="Y",
                ),
                RstrctnPrscrbngTxtRltd(
                    schedule_code=7, res_code="R1", prescribing_text_id=9, pt_position=1
                ),
                Indication(schedule_code=7, indication_prescribing_txt_id=9, condition="Condition"),
            ]
        )
        session.commit()

        assert resolve_schedule(session, "2026-02-01").schedule_code == 7
        item = find_items(session, "X1", as_of="2026-02-01")[0]
        expanded = expand_item(session, item)

    assert expanded.atc_codes[0].atc_code == "A01"
    assert expanded.restrictions[0].indications[0].condition == "Condition"


def test_indication_candidates_preserve_structured_provenance(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=8, effective_date="2026-02-01", effective_year=2026))
        session.commit()
        session.add_all(
            [
                Item(schedule_code=8, li_item_id="li-2", pbs_code="X2", drug_name="Drug"),
                RestrictionText(
                    schedule_code=8,
                    res_code="R2",
                    schedule_html_text="<p>Fallback should not be used</p>",
                ),
                PrescribingTxt(
                    schedule_code=8,
                    prescribing_txt_id=10,
                    prescribing_type="INDICATION",
                    prescribing_txt="Condition text",
                ),
            ]
        )
        session.commit()
        session.add_all(
            [
                ItemRestrictionRltd(
                    schedule_code=8,
                    pbs_code="X2",
                    res_code="R2",
                    benefit_type_code="A",
                    restriction_indicator="Y",
                ),
                RstrctnPrscrbngTxtRltd(
                    schedule_code=8,
                    res_code="R2",
                    prescribing_text_id=10,
                    pt_position=1,
                ),
                Indication(
                    schedule_code=8,
                    indication_prescribing_txt_id=10,
                    condition="Condition text",
                    episodicity="Persistent",
                    severity="Severe",
                ),
            ]
        )
        session.commit()

        candidates = indication_candidates(session, "X2", as_of="2026-02-01")

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.indication.source == "indication"
    assert candidate.indication.schedule_code == 8
    assert candidate.indication.prescribing_txt_id == 10
    assert candidate.indication.benefit_type_code is BenefitTypeCode.AUTHORITY_REQUIRED
    assert candidate.indication.episodicity == "Persistent"
    assert candidate.indication.severity == "Severe"


def test_indication_text_uses_clean_fallback_and_excludes_notes(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=9, effective_date="2026-03-01", effective_year=2026))
        session.commit()
        session.add_all(
            [
                Item(schedule_code=9, li_item_id="li-3", pbs_code="X3", drug_name="Drug"),
                RestrictionText(
                    schedule_code=9,
                    res_code="R3",
                    schedule_html_text="<p>Use&nbsp;<strong>only</strong> for &amp; condition.</p>",
                ),
                RestrictionText(
                    schedule_code=9,
                    res_code="N3",
                    schedule_html_text="<p>This is an administrative note.</p>",
                ),
            ]
        )
        session.commit()
        session.add_all(
            [
                ItemRestrictionRltd(
                    schedule_code=9,
                    pbs_code="X3",
                    res_code="R3",
                    benefit_type_code="S",
                    restriction_indicator="Y",
                ),
                ItemRestrictionRltd(
                    schedule_code=9,
                    pbs_code="X3",
                    res_code="N3",
                    benefit_type_code="S",
                    restriction_indicator="N",
                ),
            ]
        )
        session.commit()
        indications = get_item_indication_text(session, session.get(Item, (9, "li-3")))

    assert len(indications) == 1
    assert indications[0].source == "restriction_text"
    assert indications[0].text == "Use only for & condition."
    assert indications[0].prescribing_txt_id is None


def test_item_amt_hierarchy_orders_and_preserves_source_rows(session_factory):
    amt_rows = [
        (40, "MPP", "shared-code", "Same term"),
        (20, "MP", "shared-code", "Same term"),
        (30, "MPUU", "unit-code", None),
        (10, "MP", "shared-code", "Same term"),
    ]
    with session_factory() as session:
        session.add(Schedule(schedule_code=20, effective_date="2026-06-01", effective_year=2026))
        session.add_all(
            [
                Item(schedule_code=20, li_item_id="li-amt", pbs_code="AMT"),
                Item(schedule_code=20, li_item_id="li-no-mp", pbs_code="NO-MP"),
            ]
        )
        session.commit()
        session.add_all(
            ItemAmt(
                schedule_code=20,
                li_item_id="li-amt",
                pbs_concept_id=concept_id,
                concept_type_code=concept_type,
                amt_code=amt_code,
                preferred_term=term,
            )
            for concept_id, concept_type, amt_code, term in amt_rows
        )
        session.add(
            ItemAmt(
                schedule_code=20,
                li_item_id="li-no-mp",
                pbs_concept_id=50,
                concept_type_code="MPP",
            )
        )
        session.commit()

        item = session.get(Item, (20, "li-amt"))
        hierarchy = get_item_amt_hierarchy(session, item)
        no_amt_rows = get_item_amt_hierarchy(session, Item(schedule_code=20, li_item_id="absent"))
        no_mp_rows = split_mp_components(session, session.get(Item, (20, "li-no-mp")))

    assert all(isinstance(concept, ItemAmt) for concept in hierarchy)
    assert [(concept.concept_type_code, concept.pbs_concept_id) for concept in hierarchy] == [
        ("MP", 10),
        ("MP", 20),
        ("MPUU", 30),
        ("MPP", 40),
    ]
    assert [concept.amt_code for concept in hierarchy[:2]] == ["shared-code", "shared-code"]
    assert no_amt_rows == []
    assert no_mp_rows == []


def test_split_mp_components_uses_unambiguous_fields_and_preserves_terms(session_factory):
    source_rows = [
        (1, "  Aspirin + metformin  ", "aspirin + METFORMIN"),
        (2, None, "One + Two"),
        (3, "Floxacillin", "Flucloxacillin"),
        (8, None, None),
        (9, "Single component", "Single component"),
        (10, "Repeated + Repeated", "Repeated + Repeated"),
    ]
    with session_factory() as session:
        session.add(Schedule(schedule_code=21, effective_date="2026-06-01", effective_year=2026))
        session.add(Item(schedule_code=21, li_item_id="li-components", pbs_code="COMPONENTS"))
        session.flush()
        session.add_all(
            [
                ItemAmt(
                    schedule_code=21,
                    li_item_id="li-components",
                    pbs_concept_id=concept_id,
                    concept_type_code="MP",
                    preferred_term=preferred,
                    pbs_preferred_term=pbs_preferred,
                )
                for concept_id, preferred, pbs_preferred in source_rows
            ]
        )
        session.flush()
        results = split_mp_components(session, session.get(Item, (21, "li-components")))

    assert all(isinstance(result, MpComponentSplit) for result in results)
    by_concept_id = {result.pbs_concept_id: result for result in results}
    assert [result.status for result in results] == [
        "split",
        "split",
        "divergent",
        "missing",
        "single_term",
        "split",
    ]
    assert by_concept_id[1].source_field == "preferred_term"
    assert by_concept_id[1].source_term == "  Aspirin + metformin  "
    assert by_concept_id[1].component_terms == ("Aspirin", "metformin")
    assert by_concept_id[2].source_field == "pbs_preferred_term"
    assert by_concept_id[2].component_terms == ("One", "Two")
    assert by_concept_id[3].field_divergence == ("Floxacillin", "Flucloxacillin")
    assert by_concept_id[9].component_terms == ("Single component",)
    assert by_concept_id[10].component_terms == ("Repeated", "Repeated")


def test_split_mp_components_rejects_unverified_separators(session_factory):
    source_rows = [
        (4, "Formula with vitamins and minerals"),
        (5, "Estradiol (&) estradiol + dydrogesterone"),
        (6, "Drug A+Drug B"),
        (7, "Drug + "),
    ]
    with session_factory() as session:
        session.add(Schedule(schedule_code=22, effective_date="2026-06-01", effective_year=2026))
        session.add(Item(schedule_code=22, li_item_id="li-unsupported", pbs_code="UNSUPPORTED"))
        session.flush()
        session.add_all(
            [
                ItemAmt(
                    schedule_code=22,
                    li_item_id="li-unsupported",
                    pbs_concept_id=concept_id,
                    concept_type_code="MP",
                    preferred_term=term,
                    pbs_preferred_term=term,
                )
                for concept_id, term in source_rows
            ]
        )
        session.flush()
        results = split_mp_components(session, session.get(Item, (22, "li-unsupported")))

    assert [result.status for result in results] == ["unsupported"] * len(source_rows)
    assert all(not result.component_terms and result.reason for result in results)


def test_item_lookup_with_unknown_date_returns_no_items(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=7, effective_date="2026-01-01", effective_year=2026))
        session.commit()
        session.add(Item(schedule_code=7, li_item_id="li-4", pbs_code="X4", drug_name="Drug"))
        session.commit()

        assert find_items(session, "X4", as_of="2025-01-01") == []


def test_schedule_resolution_tie_breaks_by_schedule_code(session_factory):
    with session_factory() as session:
        session.add_all(
            [
                Schedule(schedule_code=10, effective_date="2026-04-01", effective_year=2026),
                Schedule(schedule_code=11, effective_date="2026-04-01", effective_year=2026),
            ]
        )
        session.commit()

        assert resolve_schedule(session, "2026-05-01").schedule_code == 11


def test_unknown_benefit_type_is_preserved(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=12, effective_date="2026-05-01", effective_year=2026))
        session.commit()
        session.add_all(
            [
                Item(schedule_code=12, li_item_id="li-5", pbs_code="X5", drug_name="Drug"),
                RestrictionText(schedule_code=12, res_code="R5", schedule_html_text="Use for condition"),
                ItemRestrictionRltd(
                    schedule_code=12,
                    pbs_code="X5",
                    res_code="R5",
                    benefit_type_code="Z",
                    restriction_indicator="Y",
                ),
            ]
        )
        session.commit()

        indications = get_item_indication_text(session, session.get(Item, (12, "li-5")))

    assert indications[0].benefit_type_code == "Z"


def test_item_manufacturer_uses_item_manufacturer_link_not_wholesaler_link(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=50, effective_date="2026-09-01", effective_year=2026))
        session.commit()
        session.add_all(
            [
                Organisation(schedule_code=50, organisation_id=1, name="Item manufacturer"),
                Organisation(schedule_code=50, organisation_id=2, name="Wholesaler"),
            ]
        )
        session.commit()
        item = Item(
            schedule_code=50,
            li_item_id="li-manufacturer",
            pbs_code="M1",
            organisation_id=1,
        )
        session.add(item)
        session.commit()
        session.add(
            ItemOrganisationRltd(schedule_code=50, pbs_code="M1", organisation_id=2)
        )
        session.commit()

        manufacturer = get_item_manufacturer(session, item)

    assert manufacturer is not None
    assert manufacturer.name == "Item manufacturer"


def test_item_criteria_breakdown_preserves_parameter_program_and_rule_context(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=51, effective_date="2026-09-01", effective_year=2026))
        session.commit()
        session.add_all(
            [
                Program(schedule_code=51, program_code="CT", program_title="Chemotherapy"),
                DispensingRule(
                    schedule_code=51,
                    dispensing_rule_mnem="HOSP",
                    dispensing_rule_title="Public hospital",
                    community_pharmacy_indicator="N",
                ),
                PrescribingTxt(
                    schedule_code=51,
                    prescribing_txt_id=100,
                    prescribing_type="CRITERIA",
                    prescribing_txt="Patient has the required clinical condition.",
                ),
                PrescribingTxt(
                    schedule_code=51,
                    prescribing_txt_id=200,
                    prescribing_type="PARAMETER",
                    prescribing_txt="Document the patient's clinical status.",
                ),
                PrescribingTxt(
                    schedule_code=51,
                    prescribing_txt_id=300,
                    prescribing_type="INDICATION",
                    prescribing_txt="Indication text is kept separate.",
                ),
            ]
        )
        session.commit()
        session.add_all(
            [
                Criteria(
                    schedule_code=51,
                    criteria_prescribing_txt_id=100,
                    criteria_type="CLINICAL_PATIENT",
                    parameter_relationship="AND",
                ),
                Parameter(
                    schedule_code=51,
                    assessment_type="CLINICAL",
                    parameter_prescribing_txt_id=200,
                    parameter_type="CLINICAL_PATIENT",
                ),
            ]
        )
        session.commit()
        session.add(
            Item(
                schedule_code=51,
                li_item_id="li-criteria",
                pbs_code="C1",
                program_code="CT",
            )
        )
        session.commit()
        session.add_all(
            [
                ItemPrescribingTxtRltd(
                    schedule_code=51,
                    pbs_code="C1",
                    prescribing_txt_id=100,
                    pt_position=1,
                ),
                ItemPrescribingTxtRltd(
                    schedule_code=51,
                    pbs_code="C1",
                    prescribing_txt_id=300,
                    pt_position=2,
                ),
                CriteriaParameterRltd(
                    schedule_code=51,
                    criteria_prescribing_txt_id=100,
                    parameter_prescribing_txt_id=200,
                    pt_position=1,
                ),
                ItemDispensingRuleRltd(
                    schedule_code=51,
                    li_item_id="li-criteria",
                    dispensing_rule_mnem="HOSP",
                ),
            ]
        )
        session.commit()

        item = session.get(Item, (51, "li-criteria"))
        result = get_item_criteria_breakdown(session, item)
        links = get_item_dispensing_rule_links(session, item)

    assert len(result.criteria) == 1
    criterion = result.criteria[0]
    assert criterion.prescribing_text.prescribing_txt.startswith("Patient has")
    assert criterion.criteria.criteria_type == "CLINICAL_PATIENT"
    assert len(criterion.parameters) == 1
    assert criterion.parameters[0].prescribing_text.prescribing_txt.startswith("Document")
    assert criterion.parameters[0].parameters[0].parameter_type == "CLINICAL_PATIENT"
    assert result.program.program_title == "Chemotherapy"
    assert [rule.dispensing_rule_mnem for rule in result.dispensing_rules] == ["HOSP"]
    assert [link.dispensing_rule_mnem for link in links] == ["HOSP"]


def test_item_pricing_breakdown_returns_source_inputs_without_calculating_patient_amount(
    session_factory,
):
    with session_factory() as session:
        session.add(Schedule(schedule_code=52, effective_date="2026-09-01", effective_year=2026))
        session.commit()
        session.add_all(
            [
                Program(schedule_code=52, program_code="CT", program_title="Chemotherapy"),
                DispensingRule(
                    schedule_code=52,
                    dispensing_rule_mnem="HOSP",
                    dispensing_rule_title="Public hospital",
                ),
            ]
        )
        session.commit()
        session.add_all(
            [
                Copayment(schedule_code=52, general=31.60, concessional=7.70),
                Fee(schedule_code=52, program_code="CT", dispensing_fee_ready_prepared=1.00),
                MarkupBand(
                    schedule_code=52,
                    program_code="CT",
                    dispensing_rule_mnem="HOSP",
                    markup_band_code="A",
                    limit=100.0,
                    variable=0.1,
                    offset=0.0,
                    fixed=1.0,
                ),
            ]
        )
        session.commit()
        session.add(
            Item(
                schedule_code=52,
                li_item_id="li-price",
                pbs_code="P1",
                program_code="CT",
            )
        )
        session.commit()
        session.add_all(
            [
                ItemDispensingRuleRltd(
                    schedule_code=52,
                    li_item_id="li-price",
                    dispensing_rule_mnem="HOSP",
                    special_patient_contribution=2.0,
                ),
                ItemPricingEvent(
                    schedule_code=52,
                    li_item_id="li-price",
                    percentage_applied=5.0,
                    event_type_code="APRIL_ADJUSTMENT",
                ),
            ]
        )
        session.commit()

        result = get_item_pricing_breakdown(session, session.get(Item, (52, "li-price")))

    assert result.copayment.general == 31.60
    assert result.fee.dispensing_fee_ready_prepared == 1.00
    assert result.dispensing_rule_links[0].special_patient_contribution == 2.0
    assert result.markup_bands[0].markup_band_code == "A"
    assert result.pricing_events[0].event_type_code == "APRIL_ADJUSTMENT"
