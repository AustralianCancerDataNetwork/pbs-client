"""Explicit SQLAlchemy models for the PBS API resources in this group."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
import sqlalchemy.orm as so

from pbs_client.db.model.base import Base, PBSRecordMixin


class ExtemporaneousDrugTariff(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /extemporaneous-tariffs."""

    __tablename__ = "pbs_extemporaneousdrugtariff"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    drug_name: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=True)
    agreed_purchasing_unit: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    markup: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    rounded_rec_one_tenth_gram: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    rounded_rec_one_gram: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    rounded_rec_ten_gram: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    rounded_rec_hundred_gram: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    exact_rec_one_tenth_gram: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    exact_rec_one_gram: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    exact_rec_ten_gram: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    exact_rec_hundred_gram: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)


class ExtemporaneousIngredient(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /extemporaneous-ingredients."""

    __tablename__ = "pbs_extemporaneousingredient"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    agreed_purchasing_unit: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    exact_tenth_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    exact_one_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    exact_ten_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    exact_hundred_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    rounded_tenth_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    rounded_one_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    rounded_ten_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    rounded_hundred_gram_per_ml_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)


class Item(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /items."""

    __tablename__ = "pbs_item"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    li_item_id: so.Mapped[str] = so.mapped_column(sa.String(214), nullable=False, primary_key=True)
    drug_name: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)
    li_drug_name: so.Mapped[str | None] = so.mapped_column(sa.String(2000), nullable=True)
    li_form: so.Mapped[str | None] = so.mapped_column(sa.String(500), nullable=True)
    schedule_form: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    brand_name: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    program_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    benefit_type_code: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    caution_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    note_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    manner_of_administration: so.Mapped[str | None] = so.mapped_column(sa.String(60), nullable=True)
    moa_preferred_term: so.Mapped[str | None] = so.mapped_column(sa.String(33), nullable=True)
    maximum_prescribable_pack: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    maximum_quantity_units: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    number_of_repeats: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    organisation_id: so.Mapped[int | None] = so.mapped_column(sa.Integer, nullable=True)
    manufacturer_code: so.Mapped[str | None] = so.mapped_column(sa.String(3), nullable=True)
    pack_size: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    pricing_quantity: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    pack_not_to_be_broken_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    claimed_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    determined_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    determined_qty: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    safety_net_resupply_rule_days: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    safety_net_resup_rule_cnt_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    extemporaneous_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    extemporaneous_standard: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    doctors_bag_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    section100_only_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    doctors_bag_only_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    brand_substitution_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    brand_substitution_group_code: so.Mapped[str | None] = so.mapped_column(
        sa.String(1), nullable=True
    )
    supply_only_indicator: so.Mapped[str | None] = so.mapped_column(sa.String(1), nullable=True)
    supply_only_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    non_effective_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    weighted_avg_disclosed_price: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    originator_brand_indicator: so.Mapped[str | None] = so.mapped_column(
        sa.String(1), nullable=True
    )
    paper_med_chart_eligible_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    elect_med_chart_eligible_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    hsptl_med_chart_eligible_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    paper_med_chart_duration: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    elect_med_chart_duration: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    hsptl_chart_acute_duration: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    hsptl_chart_sub_acute_duration: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    hsptl_chart_chronic_duration: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    pack_content: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    vial_content: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    infusible_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    unit_of_measure: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    continued_dispensing_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    continued_dispensing_emergency: so.Mapped[str | None] = so.mapped_column(
        sa.String(1), nullable=True
    )
    maximum_amount: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    formulary: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    water_added_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    section_19a_expiry_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    container_fee_type: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    policy_applied_imdq60_base_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    policy_applied_imdq60_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    policy_applied_bio_sim_up_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    policy_applied_indig_phar_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    therapeutic_exemption_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    premium_exemption_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    doctors_bag_group_title: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    therapeutic_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    therapeutic_group_title: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    advanced_notice_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    supply_only_end_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    first_listed_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    legal_unar_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    legal_car_ind: so.Mapped[str | None] = so.mapped_column(sa.String(1), nullable=True)
    proportional_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    li_substitution_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    innovator_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)


class ItemOverview(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /item-overview."""

    __tablename__ = "pbs_itemoverview"

    li_item_id: so.Mapped[str] = so.mapped_column(sa.String(214), nullable=False, primary_key=True)
    drug_name: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)
    li_drug_name: so.Mapped[str | None] = so.mapped_column(sa.String(2000), nullable=True)
    li_form: so.Mapped[str | None] = so.mapped_column(sa.String(500), nullable=True)
    schedule_form: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    brand_name: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    program_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    benefit_type_code: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    caution_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    note_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    manner_of_administration: so.Mapped[str | None] = so.mapped_column(sa.String(60), nullable=True)
    moa_preferred_term: so.Mapped[str | None] = so.mapped_column(sa.String(33), nullable=True)
    maximum_prescribable_pack: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    maximum_quantity_units: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    number_of_repeats: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    organisation_id: so.Mapped[int | None] = so.mapped_column(sa.Integer, nullable=True)
    manufacturer_code: so.Mapped[str | None] = so.mapped_column(sa.String(3), nullable=True)
    pack_size: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    pricing_quantity: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    pack_not_to_be_broken_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    claimed_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    determined_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    determined_qty: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    safety_net_resupply_rule_days: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    safety_net_resup_rule_cnt_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    extemporaneous_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    extemporaneous_standard: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    doctors_bag_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    section100_only_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    doctors_bag_only_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    brand_substitution_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    brand_substitution_group_code: so.Mapped[str | None] = so.mapped_column(
        sa.String(1), nullable=True
    )
    supply_only_indicator: so.Mapped[str | None] = so.mapped_column(sa.String(1), nullable=True)
    supply_only_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    non_effective_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    weighted_avg_disclosed_price: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    originator_brand_indicator: so.Mapped[str | None] = so.mapped_column(
        sa.String(1), nullable=True
    )
    paper_med_chart_eligible_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    elect_med_chart_eligible_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    hsptl_med_chart_eligible_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    paper_med_chart_duration: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    elect_med_chart_duration: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    hsptl_chart_acute_duration: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    hsptl_chart_sub_acute_duration: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    hsptl_chart_chronic_duration: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    pack_content: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    vial_content: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    infusible_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    unit_of_measure: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    continued_dispensing_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    continued_dispensing_emergency: so.Mapped[str | None] = so.mapped_column(
        sa.String(1), nullable=True
    )
    maximum_amount: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    formulary: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    water_added_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    section_19a_expiry_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    container_fee_type: so.Mapped[str | None] = so.mapped_column(sa.String(50), nullable=True)
    policy_applied_imdq60_base_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    policy_applied_imdq60_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    policy_applied_bio_sim_up_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    policy_applied_indig_phar_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    therapeutic_exemption_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    premium_exemption_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    doctors_bag_group_title: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    therapeutic_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    therapeutic_group_title: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    advanced_notice_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    supply_only_end_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    first_listed_date: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)
    legal_unar_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    legal_car_ind: so.Mapped[str | None] = so.mapped_column(sa.String(1), nullable=True)
    proportional_price: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    li_substitution_group_id: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    innovator_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    schedule: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    program: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    item_prescribing_texts: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    item_restrictions: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    item_atcs: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    item_amts: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    item_dispensing_rules: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    extemporaneous_ingredient: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    extemporaneous_drug_tariff: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    extemporaneous_preparation: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    extemporaneous_standard_formula_preparation: so.Mapped[Any | None] = so.mapped_column(
        sa.JSON, nullable=True
    )
    item_pricing_events: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    prescribers: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    manufacturer: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    extemporaneous_wholesalers: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)


class ItemAmt(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /amt-items."""

    __tablename__ = "pbs_itemamt"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_concept_id: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    concept_type_code: so.Mapped[str] = so.mapped_column(
        sa.String(4), nullable=False, primary_key=True
    )
    amt_code: so.Mapped[str | None] = so.mapped_column(sa.String(38), nullable=True)
    li_item_id: so.Mapped[str] = so.mapped_column(sa.String(214), nullable=False, primary_key=True)
    preferred_term: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    exempt_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    non_amt_code: so.Mapped[str | None] = so.mapped_column(sa.String(38), nullable=True)
    pbs_preferred_term: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)


class Prescriber(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /prescribers."""

    __tablename__ = "pbs_prescriber"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    prescriber_code: so.Mapped[str] = so.mapped_column(
        sa.String(10), nullable=False, primary_key=True
    )
    prescriber_type: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=True)


class StandardFormulaPreparations(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /standard-formula-preparations."""

    __tablename__ = "pbs_standardformulapreparations"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    sfp_drug_name: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=True)
    sfp_reference: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    container_fee: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    dispensing_fee_max_quantity: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    safety_net_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    maximum_patient_charge: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    maximum_quantity_unit: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    maximum_quantity: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)


__all__ = [
    "ExtemporaneousDrugTariff",
    "ExtemporaneousIngredient",
    "Item",
    "ItemAmt",
    "ItemOverview",
    "Prescriber",
    "StandardFormulaPreparations",
]
