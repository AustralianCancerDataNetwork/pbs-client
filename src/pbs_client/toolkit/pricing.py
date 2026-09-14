"""PBS pricing inputs, kept separate from clinical indication analytics."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from pbs_client.db.model import (
    Copayment,
    Fee,
    Item,
    ItemDispensingRuleRltd,
    ItemPricingEvent,
    MarkupBand,
)
from pbs_client.toolkit.core import get_item_dispensing_rule_links


@dataclass(frozen=True, slots=True)
class ItemPricingBreakdown:
    """Raw schedule-level and item-level inputs relevant to PBS pricing."""

    item: Item
    copayment: Copayment | None
    fee: Fee | None
    dispensing_rule_links: tuple[ItemDispensingRuleRltd, ...]
    markup_bands: tuple[MarkupBand, ...]
    pricing_events: tuple[ItemPricingEvent, ...]


def get_item_pricing_breakdown(session: Session, item: Item) -> ItemPricingBreakdown:
    """Return linked PBS pricing inputs without estimating a patient's payment.

    The final amount depends on patient category, dispensing circumstances,
    and applicable premiums or thresholds; this function exposes source rows
    rather than implying one universal out-of-pocket price.
    """

    copayment = session.get(Copayment, item.schedule_code)
    fee = (
        session.get(Fee, (item.schedule_code, item.program_code))
        if item.program_code is not None
        else None
    )
    dispensing_rule_links = tuple(get_item_dispensing_rule_links(session, item))
    rule_mnemonics = {link.dispensing_rule_mnem for link in dispensing_rule_links}
    markup_bands = (
        session.scalars(
            select(MarkupBand)
            .where(
                MarkupBand.schedule_code == item.schedule_code,
                MarkupBand.program_code == item.program_code,
                MarkupBand.dispensing_rule_mnem.in_(rule_mnemonics),
            )
            .order_by(MarkupBand.dispensing_rule_mnem, MarkupBand.markup_band_code)
        ).all()
        if item.program_code is not None and rule_mnemonics
        else []
    )
    pricing_events = session.scalars(
        select(ItemPricingEvent)
        .where(
            ItemPricingEvent.schedule_code == item.schedule_code,
            ItemPricingEvent.li_item_id == item.li_item_id,
        )
        .order_by(ItemPricingEvent.event_type_code, ItemPricingEvent.percentage_applied)
    ).all()
    return ItemPricingBreakdown(
        item=item,
        copayment=copayment,
        fee=fee,
        dispensing_rule_links=dispensing_rule_links,
        markup_bands=tuple(markup_bands),
        pricing_events=tuple(pricing_events),
    )


__all__ = ["ItemPricingBreakdown", "get_item_pricing_breakdown"]
