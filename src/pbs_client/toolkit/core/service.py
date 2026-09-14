"""Composable local-only navigation over PBS mirror models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from html.parser import HTMLParser
from typing import Any, Literal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from pbs_client.db.model import (
    ATC,
    Indication,
    Item,
    ItemAmt,
    ItemAtcRltd,
    ItemDispensingRuleRltd,
    ItemRestrictionRltd,
    Organisation,
    PrescribingTxt,
    RestrictionText,
    RstrctnPrscrbngTxtRltd,
    Schedule,
)


class BenefitTypeCode(str, Enum):
    """PBS restriction category recorded on a prescribing rule."""

    UNRESTRICTED = "U"
    RESTRICTED = "R"
    AUTHORITY_REQUIRED = "A"
    STREAMLINED = "S"


@dataclass(frozen=True, slots=True)
class IndicationText:
    """One traceable structured or fallback indication text value."""

    text: str
    source: Literal["indication", "restriction_text"]
    schedule_code: int
    res_code: str
    prescribing_txt_id: int | None
    benefit_type_code: BenefitTypeCode | str
    episodicity: str | None = None
    severity: str | None = None


@dataclass(frozen=True, slots=True)
class MpComponentSplit:
    """Conservative component-text interpretation of one AMT MP row."""

    schedule_code: int
    li_item_id: str
    pbs_concept_id: int
    source_field: Literal["preferred_term", "pbs_preferred_term"] | None
    source_term: str | None
    component_terms: tuple[str, ...]
    status: Literal["split", "single_term", "missing", "unsupported", "divergent"]
    reason: str | None = None
    field_divergence: tuple[str, str] | None = None


@dataclass(frozen=True, slots=True)
class RestrictionExpansion:
    restriction: RestrictionText
    prescribing_texts: list[PrescribingTxt] = field(default_factory=list)
    indications: list[Indication] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ItemExpansion:
    item: Item
    restrictions: list[RestrictionExpansion] = field(default_factory=list)
    atc_codes: list[ATC] = field(default_factory=list)


class _HTMLTextExtractor(HTMLParser):
    """Extract readable text while keeping boundaries between HTML blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "div", "li", "p", "tr"}:
            self.parts.append(" ")


_AMT_CONCEPT_TYPE_ORDER = {"MP": 0, "MPUU": 1, "MPP": 2, "TPP": 3, "TPUU": 4}
_AMT_COMPONENT_CONNECTOR = re.compile(r"\b(?:and|with)\b", re.IGNORECASE)


def _clean_html(value: str | None) -> str | None:
    if not value:
        return None
    parser = _HTMLTextExtractor()
    parser.feed(value)
    parser.close()
    text = " ".join("".join(parser.parts).split())
    return text or None


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%Y%m%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007 - date-only formats
        except ValueError:
            pass
    raise ValueError(f"cannot parse PBS date: {value!r}")


def _benefit_type(value: str | None) -> BenefitTypeCode | str:
    """Preserve an API benefit code even when a newer value is introduced."""

    if value is None:
        return "UNKNOWN"
    try:
        return BenefitTypeCode(value)
    except ValueError:
        return value


def resolve_schedule(session: Session, as_of: date | datetime | str) -> Schedule | None:
    """Resolve the latest schedule effective on ``as_of`` by date."""

    target = _as_date(as_of)
    schedules = session.scalars(select(Schedule)).all()
    eligible = [
        schedule
        for schedule in schedules
        if schedule.effective_date is not None and _as_date(schedule.effective_date) <= target
    ]
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda schedule: (_as_date(schedule.effective_date), schedule.schedule_code),
    )


def find_items(
    session: Session,
    item_code: str,
    *,
    schedule_code: int | None = None,
    as_of: date | datetime | str | None = None,
) -> list[Item]:
    """Find PBS items by code and optionally by schedule/date."""

    if as_of is not None and schedule_code is None:
        schedule = resolve_schedule(session, as_of)
        if schedule is None:
            return []
        schedule_code = schedule.schedule_code
    statement = select(Item).where(or_(Item.pbs_code == item_code, Item.li_item_id == item_code))
    if schedule_code is not None:
        statement = statement.where(Item.schedule_code == schedule_code)
    return list(session.scalars(statement).all())


def get_item(session: Session, item_code: str, **kwargs: Any) -> Item | None:
    """Return the first matching item, or ``None``."""

    return next(iter(find_items(session, item_code, **kwargs)), None)


def get_item_manufacturer(session: Session, item: Item) -> Organisation | None:
    """Return the manufacturer PBS links directly to this item, if present.

    The Item resource's ``organisation_id`` identifies its manufacturer.
    ``ItemOrganisationRltd`` describes a wholesaling relationship instead
    and is deliberately not used here.
    """

    if item.organisation_id is None:
        return None
    return session.get(Organisation, (item.schedule_code, item.organisation_id))


def get_item_restrictions(session: Session, item: Item) -> list[RestrictionExpansion]:
    """Expand an item through restrictions, prescribing text, and indications."""

    if item.pbs_code is None:
        return []
    links = session.scalars(
        select(ItemRestrictionRltd).where(
            ItemRestrictionRltd.schedule_code == item.schedule_code,
            ItemRestrictionRltd.pbs_code == item.pbs_code,
        )
    ).all()
    expansions: list[RestrictionExpansion] = []
    for link in links:
        restriction = session.get(RestrictionText, (item.schedule_code, link.res_code))
        if restriction is None:
            continue
        text_links = session.scalars(
            select(RstrctnPrscrbngTxtRltd).where(
                RstrctnPrscrbngTxtRltd.schedule_code == item.schedule_code,
                RstrctnPrscrbngTxtRltd.res_code == link.res_code,
            )
        ).all()
        texts = [
            text
            for text_link in text_links
            if (
                text := session.get(
                    PrescribingTxt,
                    (item.schedule_code, text_link.prescribing_text_id),
                )
            )
            is not None
        ]
        indications: list[Indication] = []
        for text in texts:
            indications.extend(
                session.scalars(
                    select(Indication).where(
                        Indication.schedule_code == item.schedule_code,
                        Indication.indication_prescribing_txt_id == text.prescribing_txt_id,
                    )
                ).all()
            )
        expansions.append(RestrictionExpansion(restriction, texts, indications))
    return expansions


def get_item_indication_text(session: Session, item: Item) -> list[IndicationText]:
    """Return structured indications, or explicitly-provenanced text fallbacks.

    Notes and cautions are excluded using the PBS relationship's
    ``restriction_indicator`` field. A restriction produces a fallback only
    when it has no usable linked ``INDICATION`` condition.
    """

    if item.pbs_code is None:
        return []
    links = session.scalars(
        select(ItemRestrictionRltd).where(
            ItemRestrictionRltd.schedule_code == item.schedule_code,
            ItemRestrictionRltd.pbs_code == item.pbs_code,
            ItemRestrictionRltd.restriction_indicator == "Y",
        )
    ).all()
    results: list[IndicationText] = []
    for link in links:
        restriction = session.get(RestrictionText, (item.schedule_code, link.res_code))
        if restriction is None:
            continue
        benefit_type = _benefit_type(link.benefit_type_code)
        structured = _structured_indications(session, item, link, benefit_type)
        if structured:
            results.extend(structured)
            continue
        if fallback := _fallback_indication(item, link, restriction, benefit_type):
            results.append(fallback)
    return results


def _structured_indications(
    session: Session,
    item: Item,
    link: ItemRestrictionRltd,
    benefit_type: BenefitTypeCode | str,
) -> list[IndicationText]:
    text_links = session.scalars(
        select(RstrctnPrscrbngTxtRltd)
        .where(
            RstrctnPrscrbngTxtRltd.schedule_code == item.schedule_code,
            RstrctnPrscrbngTxtRltd.res_code == link.res_code,
        )
        .order_by(RstrctnPrscrbngTxtRltd.pt_position)
    ).all()
    results: list[IndicationText] = []
    for text_link in text_links:
        prescribing_text = session.get(
            PrescribingTxt,
            (item.schedule_code, text_link.prescribing_text_id),
        )
        if prescribing_text is None or prescribing_text.prescribing_type != "INDICATION":
            continue
        indication = session.get(
            Indication,
            (item.schedule_code, prescribing_text.prescribing_txt_id),
        )
        if indication is None or not indication.condition or not indication.condition.strip():
            continue
        results.append(
            IndicationText(
                text=indication.condition.strip(),
                source="indication",
                schedule_code=item.schedule_code,
                res_code=link.res_code,
                prescribing_txt_id=prescribing_text.prescribing_txt_id,
                benefit_type_code=benefit_type,
                episodicity=indication.episodicity,
                severity=indication.severity,
            )
        )
    return results


def _fallback_indication(
    item: Item,
    link: ItemRestrictionRltd,
    restriction: RestrictionText,
    benefit_type: BenefitTypeCode | str,
) -> IndicationText | None:
    text = _clean_html(restriction.schedule_html_text) or _clean_html(restriction.li_html_text)
    if not text:
        return None
    return IndicationText(
        text=text,
        source="restriction_text",
        schedule_code=item.schedule_code,
        res_code=link.res_code,
        prescribing_txt_id=None,
        benefit_type_code=benefit_type,
    )


def get_item_atc_codes(session: Session, item: Item) -> list[ATC]:
    """Expand an item through its ATC relationship rows."""

    if item.pbs_code is None:
        return []
    links = session.scalars(
        select(ItemAtcRltd).where(
            ItemAtcRltd.schedule_code == item.schedule_code,
            ItemAtcRltd.pbs_code == item.pbs_code,
        )
    ).all()
    return [
        atc
        for link in links
        if (atc := session.get(ATC, (item.schedule_code, link.atc_code))) is not None
    ]


def get_item_dispensing_rule_links(session: Session, item: Item) -> list[ItemDispensingRuleRltd]:
    """Return the dispensing-rule relationship rows attached to an item."""

    return session.scalars(
        select(ItemDispensingRuleRltd)
        .where(
            ItemDispensingRuleRltd.schedule_code == item.schedule_code,
            ItemDispensingRuleRltd.li_item_id == item.li_item_id,
        )
        .order_by(ItemDispensingRuleRltd.dispensing_rule_mnem)
    ).all()


def get_item_amt_hierarchy(session: Session, item: Item) -> list[ItemAmt]:
    """Return every linked AMT row, keeping its PBS row identity intact."""

    rows = session.scalars(
        select(ItemAmt).where(
            ItemAmt.schedule_code == item.schedule_code,
            ItemAmt.li_item_id == item.li_item_id,
        )
    ).all()
    rows.sort(
        key=lambda row: (
            _AMT_CONCEPT_TYPE_ORDER.get(row.concept_type_code, len(_AMT_CONCEPT_TYPE_ORDER)),
            row.concept_type_code,
            row.pbs_concept_id,
        )
    )
    return rows


def _parse_mp_component_text(
    text: str,
) -> tuple[Literal["split", "single_term", "unsupported"], tuple[str, ...], str | None]:
    if "(&)" in text:
        return "unsupported", (), 'unsupported "(&)" separator'
    if _AMT_COMPONENT_CONNECTOR.search(text):
        return "unsupported", (), '"with"/"and" text is not treated as a combination'
    if "+" not in text:
        return "single_term", (text,), None

    parts = tuple(part.strip() for part in text.split(" + "))
    if len(parts) < 2 or any(not part or "+" in part for part in parts):
        return "unsupported", (), "unrecognized or empty combination component"
    return "split", parts, None


def _select_mp_source(
    concept: ItemAmt,
) -> tuple[
    Literal["preferred_term", "pbs_preferred_term"] | None,
    str | None,
    str | None,
    tuple[str, str] | None,
]:
    preferred = concept.preferred_term
    fallback = concept.pbs_preferred_term
    preferred_text = preferred.strip() if preferred and preferred.strip() else None
    fallback_text = fallback.strip() if fallback and fallback.strip() else None

    if preferred and fallback and preferred_text and fallback_text:
        normalized_preferred = " ".join(preferred_text.split()).casefold()
        normalized_fallback = " ".join(fallback_text.split()).casefold()
        if normalized_preferred != normalized_fallback:
            return None, None, None, (preferred, fallback)

    if preferred_text:
        return "preferred_term", preferred, preferred_text, None
    if fallback_text:
        return "pbs_preferred_term", fallback, fallback_text, None
    return None, None, None, None


def _split_mp_concept(concept: ItemAmt) -> MpComponentSplit:
    source_field, source_term, text, field_divergence = _select_mp_source(concept)
    component_terms: tuple[str, ...] = ()
    reason: str | None = None
    status: Literal["split", "single_term", "missing", "unsupported", "divergent"]

    if field_divergence:
        status = "divergent"
        reason = "preferred_term and pbs_preferred_term differ"
    elif text:
        status, component_terms, reason = _parse_mp_component_text(text)
    else:
        status = "missing"

    return MpComponentSplit(
        schedule_code=concept.schedule_code,
        li_item_id=concept.li_item_id,
        pbs_concept_id=concept.pbs_concept_id,
        source_field=source_field,
        source_term=source_term,
        component_terms=component_terms,
        status=status,
        reason=reason,
        field_divergence=field_divergence,
    )


def split_mp_components(session: Session, item: Item) -> list[MpComponentSplit]:
    """Return one conservative component-text result per linked MP row."""

    return [
        _split_mp_concept(concept)
        for concept in get_item_amt_hierarchy(session, item)
        if concept.concept_type_code == "MP"
    ]


def expand_item(session: Session, item: Item) -> ItemExpansion:
    """Return the complete convenience expansion for an item."""

    return ItemExpansion(
        item=item,
        restrictions=get_item_restrictions(session, item),
        atc_codes=get_item_atc_codes(session, item),
    )


item_restrictions = get_item_restrictions
item_atc_codes = get_item_atc_codes
lookup_item = get_item


__all__ = [
    "BenefitTypeCode",
    "IndicationText",
    "ItemExpansion",
    "MpComponentSplit",
    "RestrictionExpansion",
    "expand_item",
    "find_items",
    "get_item",
    "get_item_amt_hierarchy",
    "get_item_atc_codes",
    "get_item_dispensing_rule_links",
    "get_item_indication_text",
    "get_item_manufacturer",
    "get_item_restrictions",
    "item_atc_codes",
    "item_restrictions",
    "lookup_item",
    "resolve_schedule",
    "split_mp_components",
]
