"""Explicit SQLAlchemy models for the PBS API resources in this group."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
import sqlalchemy.orm as so

from pbs_client.db.model.base import Base, PBSRecordMixin


class ApiChangelog(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /."""

    __tablename__ = "pbs_apichangelog"

    api_name: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False, primary_key=True)
    api_version: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False, primary_key=True)
    api_released: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)
    api_documentation: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)
    api_status: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)
    changelogs: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)


class ATC(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /atc-codes."""

    __tablename__ = "pbs_atc"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    atc_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    atc_description: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)
    atc_level: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    atc_parent_code: so.Mapped[str | None] = so.mapped_column(sa.String(10), nullable=True)


class Container(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /containers."""

    __tablename__ = "pbs_container"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    container_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    container_name: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)
    mark_up: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    agreed_purchasing_unit: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    average_exact_unit_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    average_rounded_unit_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    container_type: so.Mapped[str] = so.mapped_column(sa.String(33), nullable=True)
    container_quantity: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    container_unit_of_measure: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)


class Copayment(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /copayments."""

    __tablename__ = "pbs_copayment"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    general: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    concessional: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    safety_net_general: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    safety_net_concessional: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    safety_net_card_issue: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    increased_discount_limit: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    safety_net_ctg_contribution: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)


class Criteria(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /criteria."""

    __tablename__ = "pbs_criteria"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    criteria_prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    criteria_type: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=True)
    parameter_relationship: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)


class DispensingRule(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /dispensing-rules."""

    __tablename__ = "pbs_dispensingrule"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    dispensing_rule_mnem: so.Mapped[str] = so.mapped_column(
        sa.String(100), nullable=False, primary_key=True
    )
    dispensing_rule_reference: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=True)
    dispensing_rule_title: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=True)
    community_pharmacy_indicator: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)


class ExtemporaneousPreparation(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /extemporaneous-preparations."""

    __tablename__ = "pbs_extemporaneouspreparation"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    preparation: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=True)
    maximum_quantity: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    pbs_code: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False, primary_key=True)
    maximum_quantity_unit: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)


class Fee(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /fees."""

    __tablename__ = "pbs_fee"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    program_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    dispensing_fee_ready_prepared: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    dispensing_fee_dangerous_drug: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    dispensing_fee_extra: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    dispensing_fee_extemporaneous: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    safety_net_recording_fee_ep: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    safety_net_recording_fee_rp: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    dispensing_fee_water_added: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    container_fee_injectable: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    container_fee_other: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    gnrl_copay_discount_general: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    gnrl_copay_discount_hospital: so.Mapped[float | None] = so.mapped_column(
        sa.Float, nullable=True
    )
    con_copay_discount_general: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    con_copay_discount_hospital: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    efc_diluent_fee: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    efc_preparation_fee: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    efc_distribution_fee: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    acss_imdq60_payment: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    acss_payment: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)


class Indication(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /indications."""

    __tablename__ = "pbs_indication"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    indication_prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    condition: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)
    episodicity: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    severity: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)


class Organisation(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /organisations."""

    __tablename__ = "pbs_organisation"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    organisation_id: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(4000), nullable=True)
    abn: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    street_address: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)
    city: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    state: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    postcode: so.Mapped[str | None] = so.mapped_column(sa.String(30), nullable=True)
    telephone_number: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    facsimile_number: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)


class Parameter(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /parameters."""

    __tablename__ = "pbs_parameter"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    assessment_type: so.Mapped[str] = so.mapped_column(
        sa.String(20), nullable=False, primary_key=True
    )
    parameter_prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    parameter_type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)


class PrescribingTxt(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /prescribing-texts."""

    __tablename__ = "pbs_prescribingtxt"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    prescribing_txt_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    prescribing_type: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=True)
    prescribing_txt: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    prscrbg_txt_html: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    complex_authority_rqrd_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    assessment_type_code: so.Mapped[str | None] = so.mapped_column(sa.String(20), nullable=True)
    apply_to_increase_mq_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    apply_to_increase_nr_flag: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)


class Program(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /programs."""

    __tablename__ = "pbs_program"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    program_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    program_title: so.Mapped[str] = so.mapped_column(sa.String(400), nullable=True)


class ProgramDispensingRules(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /program-dispensing-rules."""

    __tablename__ = "pbs_programdispensingrules"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    program_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    dispensing_rule_mnem: so.Mapped[str] = so.mapped_column(
        sa.String(100), nullable=False, primary_key=True
    )
    default_indicator: so.Mapped[str | None] = so.mapped_column(sa.String(1), nullable=True)


class RestrictionText(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /restrictions."""

    __tablename__ = "pbs_restrictiontext"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    res_code: so.Mapped[str] = so.mapped_column(sa.String(83), nullable=False, primary_key=True)
    treatment_phase: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    authority_method: so.Mapped[str | None] = so.mapped_column(sa.String(4000), nullable=True)
    treatment_of_code: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    restriction_number: so.Mapped[float | None] = so.mapped_column(sa.Float, nullable=True)
    li_html_text: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)
    schedule_html_text: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    note_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    caution_indicator: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    complex_authority_rqrd_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    assessment_type_code: so.Mapped[str | None] = so.mapped_column(sa.String(20), nullable=True)
    criteria_relationship: so.Mapped[str | None] = so.mapped_column(sa.String(20), nullable=True)
    variation_rule_applied: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    first_listing_date: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    written_authority_required: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)


class Schedule(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /schedules."""

    __tablename__ = "pbs_schedule"

    revision_number: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    start_tsp: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    effective_date: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    effective_month: so.Mapped[str] = so.mapped_column(sa.String(9), nullable=True)
    effective_year: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    publication_status: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)
    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)


__all__ = [
    "ATC",
    "ApiChangelog",
    "Container",
    "Copayment",
    "Criteria",
    "DispensingRule",
    "ExtemporaneousPreparation",
    "Fee",
    "Indication",
    "Organisation",
    "Parameter",
    "PrescribingTxt",
    "Program",
    "ProgramDispensingRules",
    "RestrictionText",
    "Schedule",
]
