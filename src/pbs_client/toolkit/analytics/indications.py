"""Indication-candidate composition for PBS items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from pbs_client.db.model import Item, Schedule
from pbs_client.toolkit.core import IndicationText, find_items, get_item_indication_text


@dataclass(frozen=True, slots=True)
class IndicationCandidate:
    """A PBS item, its schedule, and one traceable indication value."""

    item: Item
    schedule: Schedule
    indication: IndicationText


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


__all__ = ["IndicationCandidate", "indication_candidates"]
