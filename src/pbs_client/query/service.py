"""Read-only, local-only convenience queries over the PBS mirror."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

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


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)
    for parser in (date.fromisoformat,):
        try:
            return parser(text)
        except ValueError:
            pass
    for fmt in ("%d/%m/%Y", "%Y%m%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007 - date-only formats
        except ValueError:
            pass
    raise ValueError(f"cannot parse PBS date: {value!r}")


def resolve_schedule(session: Session, as_of: date | datetime | str) -> Schedule | None:
    """Resolve the latest schedule effective on ``as_of`` by date."""

    target = _as_date(as_of)
    schedules = session.scalars(select(Schedule)).all()
    eligible = [schedule for schedule in schedules if _as_date(schedule.effective_date) <= target]
    return max(eligible, key=lambda schedule: _as_date(schedule.effective_date), default=None)


def find_items(
    session: Session,
    item_code: str,
    *,
    schedule_code: float | None = None,
    as_of: date | datetime | str | None = None,
) -> list[Item]:
    """Find PBS items by ``pbs_code`` and optionally by schedule/date."""

    if as_of is not None and schedule_code is None:
        schedule = resolve_schedule(session, as_of)
        schedule_code = schedule.schedule_code if schedule else None
    statement = select(Item).where(or_(Item.pbs_code == item_code, Item.li_item_id == item_code))
    if schedule_code is not None:
        statement = statement.where(Item.schedule_code == schedule_code)
    return list(session.scalars(statement).all())


def get_item(session: Session, item_code: str, **kwargs: Any) -> Item | None:
    """Return the first matching item, or ``None``."""

    return next(iter(find_items(session, item_code, **kwargs)), None)


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
            if (text := session.get(
                PrescribingTxt,
                (item.schedule_code, text_link.prescribing_text_id),
            ))
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


def expand_item(session: Session, item: Item) -> ItemExpansion:
    """Return the complete v1 convenience expansion for an item."""

    return ItemExpansion(
        item=item,
        restrictions=get_item_restrictions(session, item),
        atc_codes=get_item_atc_codes(session, item),
    )


# Friendly aliases for downstream callers that prefer verb-based names.
item_restrictions = get_item_restrictions
item_atc_codes = get_item_atc_codes
lookup_item = get_item
