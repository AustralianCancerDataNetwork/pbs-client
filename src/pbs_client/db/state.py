"""Checkpoint state for resumable syncs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pbs_client.db.model import Base


class SyncState(Base):
    """One checkpoint row per mirrored resource."""

    __tablename__ = "sync_state"

    resource: Mapped[str] = mapped_column(String(100), primary_key=True)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    records_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    def begin(self) -> None:
        self.status = "in_progress"
        self.started_at = datetime.now(timezone.utc)
        self.last_error = None

    def checkpoint(self, page: int, count: int, metadata: dict[str, Any]) -> None:
        self.page = page
        self.records_written += count
        self.metadata_json = metadata

    def complete(self) -> None:
        self.status = "complete"
        self.completed_at = datetime.now(timezone.utc)
