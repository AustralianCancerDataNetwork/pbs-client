"""Explicit SQLAlchemy models for the PBS API resources in this group."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
import sqlalchemy.orm as so

from pbs_client.db.model.base import Base, PBSRecordMixin


class MarkupBand(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /markup-bands."""

    __tablename__ = "pbs_markupband"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    program_code: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    dispensing_rule_mnem: so.Mapped[str] = so.mapped_column(
        sa.String(100), nullable=False, primary_key=True
    )
    markup_band_code: so.Mapped[str] = so.mapped_column(
        sa.String(50), nullable=False, primary_key=True
    )
    limit: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    variable: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    offset: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    fixed: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)


class SummaryOfChanges(PBSRecordMixin, Base):
    """PBS API resource mirrored from endpoint /summary-of-changes."""

    __tablename__ = "pbs_summaryofchanges"

    schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, primary_key=True)
    source_schedule_code: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    target_effective_date: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)
    source_effective_date: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)
    target_revision_number: so.Mapped[int] = so.mapped_column(
        sa.Integer, nullable=False, primary_key=True
    )
    source_revision_number: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    target_publication_status: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)
    source_publication_status: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)
    changed_table: so.Mapped[str] = so.mapped_column(
        sa.String(50), nullable=False, primary_key=True
    )
    changed_endpoint: so.Mapped[str | None] = so.mapped_column(sa.String(100), nullable=True)
    change_type: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False, primary_key=True)
    # The API exposes no stable change identifier. Multiple changes can share
    # the schedule, revision, table, and change type, so the SQL statement is
    # retained as the remaining row-level discriminator.
    sql_statement: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False, primary_key=True)
    table_keys: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    change_detail: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    previous_detail: so.Mapped[Any | None] = so.mapped_column(sa.JSON, nullable=True)
    deleted_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    new_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)
    modified_ind: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)


__all__ = ["MarkupBand", "SummaryOfChanges"]
