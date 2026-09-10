from __future__ import annotations

from pbs_client.db.model import (
    ATC,
    Indication,
    Item,
    ItemAtcRltd,
    ItemRestrictionRltd,
    PrescribingTxt,
    RestrictionText,
    RstrctnPrscrbngTxtRltd,
    Schedule,
)
from pbs_client.toolkit.analytics import indication_candidates
from pbs_client.toolkit.core import (
    BenefitTypeCode,
    expand_item,
    find_items,
    get_item_indication_text,
    resolve_schedule,
)


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


def test_item_lookup_with_unknown_date_returns_no_items(session_factory):
    with session_factory() as session:
        session.add(Schedule(schedule_code=7, effective_date="2026-01-01", effective_year=2026))
        session.commit()
        session.add(Item(schedule_code=7, li_item_id="li-4", pbs_code="X4", drug_name="Drug"))
        session.commit()

        assert find_items(session, "X4", as_of="2025-01-01") == []
