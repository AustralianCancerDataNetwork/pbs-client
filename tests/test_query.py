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
from pbs_client.query import expand_item, find_items, resolve_schedule


def test_offline_item_restriction_and_atc_expansion(session_factory):
    with session_factory() as session:
        session.add_all(
            [
                Schedule(schedule_code=7, effective_date="2026-01-01", effective_year=2026, revision_number=1, start_tsp="2026-01-01T00:00:00Z", effective_month="January", publication_status="PUBLISHED"),
                Item(schedule_code=7, li_item_id="li-1", pbs_code="X1", drug_name="Drug"),
                ATC(schedule_code=7, atc_code="A01", atc_description="Example", atc_level=1),
                ItemAtcRltd(schedule_code=7, pbs_code="X1", atc_code="A01", atc_priority_pct=100),
                RestrictionText(schedule_code=7, res_code="R1", schedule_html_text="Use for indication", note_indicator="N", caution_indicator="N", complex_authority_rqrd_ind="N", variation_rule_applied="N", first_listing_date="2026-01-01", written_authority_required="N"),
                ItemRestrictionRltd(schedule_code=7, pbs_code="X1", res_code="R1", benefit_type_code="R", restriction_indicator="Y"),
                PrescribingTxt(schedule_code=7, prescribing_txt_id=9, prescribing_type="INDICATION", prescribing_txt="Text", prscrbg_txt_html="<p>Text</p>", complex_authority_rqrd_ind="N", apply_to_increase_mq_flag="N", apply_to_increase_nr_flag="N"),
                RstrctnPrscrbngTxtRltd(schedule_code=7, res_code="R1", prescribing_text_id=9, pt_position=1),
                Indication(schedule_code=7, indication_prescribing_txt_id=9, condition="Condition"),
            ]
        )
        session.commit()

        assert resolve_schedule(session, "2026-02-01").schedule_code == 7
        item = find_items(session, "X1", as_of="2026-02-01")[0]
        expanded = expand_item(session, item)

    assert expanded.atc_codes[0].atc_code == "A01"
    assert expanded.restrictions[0].indications[0].condition == "Condition"
