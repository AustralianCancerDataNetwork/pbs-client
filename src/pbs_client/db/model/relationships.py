"""Explicit SQLAlchemy models for the PBS API resources in this group."""

from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so

from pbs_client.db.model.base import Base, PBSRecordMixin


class ContainerWholesalerRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /container-organisation-relationships."""

    __tablename__ = "pbs_containerwholesaler_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    container_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    organisation_id: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)


class CriteriaParameterRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /criteria-parameter-relationships."""

    __tablename__ = "pbs_criteriaparameter_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    criteria_prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    parameter_prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    pt_position: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)


class ExPrepSfpRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /extemporaneous-prep-sfp-relationships."""

    __tablename__ = "pbs_exprepsfp_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    sfp_pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    ex_prep_pbs_code: so.Mapped[str] = so.mapped_column(
        sa.String(50), nullable=False, primary_key=True
    )


class ItemAtcRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-atc-relationships."""

    __tablename__ = "pbs_itematc_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    atc_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    atc_priority_pct: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)


class ItemDispensingRuleRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-dispensing-rule-relationships."""

    __tablename__ = "pbs_itemdispensingrule_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    li_item_id: so.Mapped[str] = so.mapped_column(sa.String(214), nullable=False, primary_key=True)
    dispensing_rule_mnem: so.Mapped[str] = so.mapped_column(
        sa.String(100), nullable=False, primary_key=True
    )
    dispensing_rule_reference: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=True)
    brand_premium: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    dispense_fee_type_code: so.Mapped[str] = so.mapped_column(sa.String(2), nullable=True)
    dangerous_drug_fee_code: so.Mapped[str | None] = so.mapped_column(sa.String(2), nullable=True)
    therapeutic_group_premium: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    cmnwlth_price_to_pharmacist: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    man_price_to_pharmacist: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    man_dispnsd_price_max_qty: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    max_record_val_for_safety_net: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    cmnwlth_dsp_price_max_qty: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    tgm_price_phrmcst: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    tgm_disp_price_max_qty: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    special_patient_contribution: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    fee_dispensing: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_dispensing_ex: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_dispensing_dd: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_water: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_container_injectable: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_container_other: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_safety_net_recording: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_safety_net_recording_ex: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_extra: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_chemo_flat_wholesale: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_chemo_prep: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    fee_diluent: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    submitted_pharmacists_pack_price: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    max_general_patient_charge: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    mn_price_dispenser: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    mn_price_wholesale_markup_limit: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    mn_price_wholesale_markup_code: so.Mapped[str | None] = so.mapped_column(
        sa.String(50), nullable=True
    )
    mn_price_wholesale_markup: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    mn_pharmacy_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    mn_pharmacy_markup_limit: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    mn_pharmacy_markup_code: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    mn_pharmacy_markup: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)


class ItemOrganisationRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-organisation-relationships."""

    __tablename__ = "pbs_itemorganisation_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    organisation_id: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)


class ItemPrescribingTxtRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-prescribing-text-relationships."""

    __tablename__ = "pbs_itemprescribingtxt_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    pt_position: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)


class ItemPricingEvent(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-pricing-events."""

    __tablename__ = "pbs_itempricingevent"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    li_item_id: so.Mapped[str] = so.mapped_column(sa.String(214), nullable=False, primary_key=True)
    percentage_applied: so.Mapped[float] = so.mapped_column(
        sa.Float, nullable=False, primary_key=True
    )
    event_type_code: so.Mapped[str] = so.mapped_column(
        sa.String(50), nullable=False, primary_key=True
    )


class ItemRestrictionRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-restriction-relationships."""

    __tablename__ = "pbs_itemrestriction_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    res_code: so.Mapped[str] = so.mapped_column(sa.String(83), nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    benefit_type_code: so.Mapped[str] = so.mapped_column(
        sa.String(1), nullable=False, primary_key=True
    )
    restriction_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    res_position: so.Mapped[int | None] = so.mapped_column(sa.Integer, nullable=True)


class RstrctnPrscrbngTxtRltd(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /restriction-prescribing-text-relationships."""

    __tablename__ = "pbs_rstrctnprscrbngtxt_rltd"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    res_code: so.Mapped[str] = so.mapped_column(sa.String(83), nullable=False, primary_key=True)
    prescribing_text_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    pt_position: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)


__all__ = [
    "ContainerWholesalerRltd",
    "CriteriaParameterRltd",
    "ExPrepSfpRltd",
    "ItemAtcRltd",
    "ItemDispensingRuleRltd",
    "ItemOrganisationRltd",
    "ItemPrescribingTxtRltd",
    "ItemPricingEvent",
    "ItemRestrictionRltd",
    "RstrctnPrscrbngTxtRltd",
]
