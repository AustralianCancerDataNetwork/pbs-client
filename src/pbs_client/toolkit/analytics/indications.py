"""Indication-candidate composition for PBS items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from pbs_client.db.model import (
    Criteria,
    CriteriaParameterRltd,
    DispensingRule,
    Item,
    ItemPrescribingTxtRltd,
    Parameter,
    PrescribingTxt,
    Program,
    Schedule,
)
from pbs_client.toolkit.core import (
    IndicationText,
    find_items,
    get_item_dispensing_rule_links,
    get_item_indication_text,
)


@dataclass(frozen=True, slots=True)
class IndicationCandidate:
    """A PBS item, its schedule, and one traceable indication value."""

    item: Item
    schedule: Schedule
    indication: IndicationText


@dataclass(frozen=True, slots=True)
class ParameterText:
    """A parameter text and all structured PBS parameter rows that describe it."""

    relationship: CriteriaParameterRltd
    prescribing_text: PrescribingTxt
    parameters: tuple[Parameter, ...]


@dataclass(frozen=True, slots=True)
class CriteriaText:
    """One item-linked eligibility criterion with its linked parameter detail."""

    item_relationship: ItemPrescribingTxtRltd
    criteria: Criteria
    prescribing_text: PrescribingTxt
    parameters: tuple[ParameterText, ...]


@dataclass(frozen=True, slots=True)
class ItemCriteriaBreakdown:
    """Clinical criteria plus separate funding and dispensing context for an item."""

    criteria: tuple[CriteriaText, ...]
    program: Program | None
    dispensing_rules: tuple[DispensingRule, ...]


def get_item_criteria_breakdown(session: Session, item: Item) -> ItemCriteriaBreakdown:
    """Return an item's linked eligibility text and separate program/rule context.

    Criteria and parameter text remain PBS-native source rows with their
    relationship metadata intact. Program and dispensing-rule values are
    returned as administrative context, not interpreted as clinical criteria.
    """

    criteria_rows = []
    if item.pbs_code is not None:
        criteria_rows = session.execute(
            select(ItemPrescribingTxtRltd, Criteria, PrescribingTxt)
            .join(
                PrescribingTxt,
                and_(
                    PrescribingTxt.schedule_code == ItemPrescribingTxtRltd.schedule_code,
                    PrescribingTxt.prescribing_txt_id == ItemPrescribingTxtRltd.prescribing_txt_id,
                ),
            )
            .join(
                Criteria,
                and_(
                    Criteria.schedule_code == PrescribingTxt.schedule_code,
                    Criteria.criteria_prescribing_txt_id == PrescribingTxt.prescribing_txt_id,
                ),
            )
            .where(
                ItemPrescribingTxtRltd.schedule_code == item.schedule_code,
                ItemPrescribingTxtRltd.pbs_code == item.pbs_code,
                PrescribingTxt.prescribing_type == "CRITERIA",
            )
            .order_by(
                ItemPrescribingTxtRltd.pt_position,
                ItemPrescribingTxtRltd.prescribing_txt_id,
            )
        ).all()

    criteria_ids = sorted(
        {criteria.criteria_prescribing_txt_id for _, criteria, _ in criteria_rows}
    )
    parameter_rows = []
    parameters_by_text_id: dict[int, list[Parameter]] = {}
    if criteria_ids:
        parameter_rows = session.execute(
            select(CriteriaParameterRltd, PrescribingTxt)
            .join(
                PrescribingTxt,
                and_(
                    PrescribingTxt.schedule_code == CriteriaParameterRltd.schedule_code,
                    PrescribingTxt.prescribing_txt_id
                    == CriteriaParameterRltd.parameter_prescribing_txt_id,
                ),
            )
            .where(
                CriteriaParameterRltd.schedule_code == item.schedule_code,
                CriteriaParameterRltd.criteria_prescribing_txt_id.in_(criteria_ids),
            )
            .order_by(
                CriteriaParameterRltd.criteria_prescribing_txt_id,
                CriteriaParameterRltd.pt_position,
                CriteriaParameterRltd.parameter_prescribing_txt_id,
            )
        ).all()
        parameter_ids = sorted(
            {relationship.parameter_prescribing_txt_id for relationship, _ in parameter_rows}
        )
        if parameter_ids:
            for parameter in session.scalars(
                select(Parameter)
                .where(
                    Parameter.schedule_code == item.schedule_code,
                    Parameter.parameter_prescribing_txt_id.in_(parameter_ids),
                )
                .order_by(
                    Parameter.parameter_prescribing_txt_id,
                    Parameter.assessment_type,
                )
            ).all():
                parameters_by_text_id.setdefault(
                    parameter.parameter_prescribing_txt_id, []
                ).append(parameter)

    parameters_by_criteria_id: dict[int, list[ParameterText]] = {}
    for relationship, prescribing_text in parameter_rows:
        parameters_by_criteria_id.setdefault(
            relationship.criteria_prescribing_txt_id, []
        ).append(
            ParameterText(
                relationship=relationship,
                prescribing_text=prescribing_text,
                parameters=tuple(
                    parameters_by_text_id.get(relationship.parameter_prescribing_txt_id, ())
                ),
            )
        )

    criteria = tuple(
        CriteriaText(
            item_relationship=item_relationship,
            criteria=criterion,
            prescribing_text=prescribing_text,
            parameters=tuple(
                parameters_by_criteria_id.get(criterion.criteria_prescribing_txt_id, ())
            ),
        )
        for item_relationship, criterion, prescribing_text in criteria_rows
    )
    program = (
        session.get(Program, (item.schedule_code, item.program_code))
        if item.program_code is not None
        else None
    )
    dispensing_rule_links = get_item_dispensing_rule_links(session, item)
    rule_mnemonics = {link.dispensing_rule_mnem for link in dispensing_rule_links}
    dispensing_rules = (
        session.scalars(
            select(DispensingRule)
            .where(
                DispensingRule.schedule_code == item.schedule_code,
                DispensingRule.dispensing_rule_mnem.in_(rule_mnemonics),
            )
            .order_by(DispensingRule.dispensing_rule_mnem)
        ).all()
        if rule_mnemonics
        else []
    )
    return ItemCriteriaBreakdown(
        criteria=criteria,
        program=program,
        dispensing_rules=tuple(dispensing_rules),
    )


def indication_candidates(
    session: Session,
    item_code: str,
    *,
    as_of: date | datetime | str | None = None,
) -> list[IndicationCandidate]:
    """Resolve an item code to all structured or fallback indications.

    With ``as_of``, item lookup is restricted to the schedule effective on
    that date. Without it, every matching historical schedule remains
    distinct. The local mirror's schedule row is paired using the item's
    opaque ``schedule_code`` rather than schedule-code magnitude.
    """

    candidates: list[IndicationCandidate] = []
    for item in find_items(session, item_code, as_of=as_of):
        schedule = session.get(Schedule, item.schedule_code)
        if schedule is None:
            continue
        candidates.extend(
            IndicationCandidate(item=item, schedule=schedule, indication=indication)
            for indication in get_item_indication_text(session, item)
        )
    return candidates


__all__ = [
    "CriteriaText",
    "IndicationCandidate",
    "ItemCriteriaBreakdown",
    "ParameterText",
    "get_item_criteria_breakdown",
    "indication_candidates",
]
