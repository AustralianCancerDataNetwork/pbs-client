"""Dependency-ordered, resumable synchronization into the local mirror."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pbs_client.db import MODEL_BY_NAME, RESOURCE_BY_NAME, RESOURCE_SPECS, SYNC_ORDER, SyncState
from pbs_client.db.model import Base
from pbs_client.errors import PBSSyncError
from pbs_client.http import PBSClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SyncResult:
    resource: str
    pages: int
    records_written: int
    status: str


def upsert_records(session: Session, model: type[Base], records: Iterable[dict[str, Any]]) -> int:
    """Insert or update records using the model's declared natural key."""

    fields = tuple(
        column.name for column in model.__table__.columns if column.name != "raw_payload"
    )
    primary_key = tuple(column.name for column in model.__table__.primary_key.columns)
    written = 0
    for record in records:
        if not isinstance(record, dict):
            raise PBSSyncError(f"{model.__name__} returned a non-object record")
        missing = [key for key in primary_key if record.get(key) is None]
        if missing:
            raise PBSSyncError(
                f"{model.__name__} record has no value for key(s): {', '.join(missing)}"
            )
        values = {field: record.get(field) for field in fields}
        values["raw_payload"] = dict(record)
        identity = tuple(values[key] for key in primary_key)
        current = session.get(model, identity if len(identity) > 1 else identity[0])
        if current is None:
            session.add(model(**values))
        else:
            for field, value in values.items():
                setattr(current, field, value)
        written += 1
    return written


class SyncOrchestrator:
    """Coordinate API pages and local transactions in the required order."""

    def __init__(self, client: PBSClient, session_factory: Callable[[], Session]) -> None:
        self.client = client
        self.session_factory = session_factory

    def run(
        self,
        *,
        resource: str | None = None,
        limit: int = 100_000,
        refresh_completed: bool = True,
    ) -> list[SyncResult]:
        """Sync all resources, or one named resource, and return page summaries.

        An incomplete resource resumes at the page after its last committed
        checkpoint.  A completed resource is refreshed from page one by
        default so newly published schedules are discovered; upsert semantics
        keep that refresh idempotent.
        """

        names = self._resource_names(resource)
        results: list[SyncResult] = []
        for name in names:
            state = self._get_or_create_state(name)
            if state.status == "complete" and not refresh_completed:
                results.append(SyncResult(name, state.page, state.records_written, state.status))
                continue
            results.append(self._sync_resource(name, state, limit=limit))
        return results

    def _sync_resource(self, name: str, state: SyncState, *, limit: int) -> SyncResult:
        spec = RESOURCE_BY_NAME[name]
        model = MODEL_BY_NAME[name]
        start_page = state.page + 1 if state.status in {"in_progress", "failed"} else 1
        if start_page == 1:
            state.page = 0
            state.records_written = 0
        state.begin()
        self._save_state(state)
        pages = 0
        try:
            for page in self.client.iter_pages(spec.endpoint, limit=limit, start_page=start_page):
                pages += 1
                with self.session_factory() as session:
                    current = session.get(SyncState, name)
                    if current is None:
                        raise PBSSyncError(f"sync state disappeared for {name}")
                    count = upsert_records(session, model, page.records)
                    metadata = {
                        "total_records": page.total_records,
                        "messages": page.messages,
                        "links": page.links,
                        "synced_at": page.metadata.get("synced_at"),
                    }
                    current.checkpoint(page.page, count, metadata)
                    session.commit()
                    state = current
                logger.info("Synced %s page %s (%s records)", name, page.page, count)
            state.complete()
            self._save_state(state)
        except Exception as exc:
            logger.exception("PBS sync failed for %s", name)
            with self.session_factory() as session:
                current = session.get(SyncState, name)
                if current is not None:
                    current.status = "failed"
                    current.last_error = str(exc)
                    session.commit()
            if isinstance(exc, PBSSyncError):
                if exc.resource is None:
                    raise PBSSyncError(str(exc), resource=name) from exc
                raise
            raise PBSSyncError(f"sync failed for {name}: {exc}", resource=name) from exc
        return SyncResult(name, state.page, state.records_written, state.status)

    def _get_or_create_state(self, name: str) -> SyncState:
        spec = RESOURCE_BY_NAME[name]
        with self.session_factory() as session:
            state = session.get(SyncState, name)
            if state is None:
                state = SyncState(resource=name, endpoint=spec.endpoint)
                session.add(state)
                session.commit()
            return state

    def _save_state(self, state: SyncState) -> None:
        with self.session_factory() as session:
            current = session.get(SyncState, state.resource)
            if current is None:
                session.add(state)
            else:
                current.page = state.page
                current.status = state.status
                current.records_written = state.records_written
                current.started_at = state.started_at
                current.completed_at = state.completed_at
                current.last_error = state.last_error
                current.metadata_json = state.metadata_json
            session.commit()

    @staticmethod
    def _resource_names(resource: str | None) -> tuple[str, ...]:
        if resource is None:
            return SYNC_ORDER
        value = resource.strip()
        if value in RESOURCE_BY_NAME:
            return (value,)
        lowered = value.lower()
        matches = tuple(spec.name for spec in RESOURCE_SPECS if spec.name.lower() == lowered)
        if matches:
            return matches
        endpoint_matches = tuple(
            spec.name
            for spec in RESOURCE_SPECS
            if spec.endpoint.strip("/").lower() == value.strip("/").lower()
        )
        if endpoint_matches:
            return endpoint_matches
        raise PBSSyncError(f"unknown PBS resource: {resource}")


def mirror_status(session: Session) -> list[dict[str, Any]]:
    """Return checkpoint and row-count information for the CLI."""

    rows: list[dict[str, Any]] = []
    for spec in RESOURCE_SPECS:
        model = MODEL_BY_NAME[spec.name]
        state = session.get(SyncState, spec.name)
        count = session.scalar(select(func.count()).select_from(model)) or 0
        rows.append(
            {
                "resource": spec.name,
                "rows": count,
                "status": state.status if state else "pending",
                "page": state.page if state else 0,
                "completed_at": state.completed_at if state else None,
            }
        )
    return rows
