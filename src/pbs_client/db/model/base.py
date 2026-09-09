"""Declarative base and shared PBS model concerns."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
import sqlalchemy.orm as so


class Base(so.DeclarativeBase):
    """Declarative registry for the local PBS mirror."""


class PBSRecordMixin:
    """Retain the original API object for forward-compatible fields."""

    raw_payload: so.Mapped[dict[str, Any]] = so.mapped_column(sa.JSON, nullable=False, default=dict)
