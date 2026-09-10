from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from pbs_client.db import init_db
from pbs_client.db.engine import fk_checks_disabled_for_refresh
from pbs_client.db.model import ItemAtcRltd
from pbs_client.errors import PBSSyncError
from pbs_client.http import Page
from pbs_client.sync import SyncOrchestrator


def orphan_item_atc(code: str) -> dict[str, object]:
    return {
        "schedule_code": 1,
        "atc_code": code,
        "pbs_code": f"PBS-{code}",
        "raw_payload": {},
    }


def test_sqlite_refresh_disables_fk_for_all_pool_connections_and_restores(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pbs.sqlite'}",
        future=True,
        pool_size=2,
        max_overflow=0,
    )
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    with fk_checks_disabled_for_refresh(engine):
        first, second = sessions(), sessions()
        try:
            first.add(ItemAtcRltd(**orphan_item_atc("A")))
            first.commit()
            second.add(ItemAtcRltd(**orphan_item_atc("B")))
            second.commit()
            assert first.execute(text("PRAGMA foreign_keys")).scalar_one() == 0
            assert second.execute(text("PRAGMA foreign_keys")).scalar_one() == 0
        finally:
            first.close()
            second.close()

    with sessions() as session:
        assert session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        session.add(ItemAtcRltd(**orphan_item_atc("C")))
        with pytest.raises(IntegrityError):
            session.commit()


class OnePageClient:
    def iter_pages(self, endpoint, *, limit, start_page):
        yield Page(endpoint, 1, 1, [orphan_item_atc("SYNC")], {"total_records": 1}, [])


class FailingClient:
    def iter_pages(self, endpoint, *, limit, start_page):
        raise RuntimeError("refresh interrupted")
        yield  # pragma: no cover


def test_orchestrator_restores_fk_enforcement_after_success_and_failure(session_factory):
    client = OnePageClient()
    orchestrator = SyncOrchestrator(client, session_factory)
    result = orchestrator.run(resource="ItemAtcRltd", limit=1)
    assert result[0].status == "complete"

    with session_factory() as session:
        session.add(ItemAtcRltd(**orphan_item_atc("AFTER")))
        with pytest.raises(IntegrityError):
            session.commit()

    with pytest.raises(PBSSyncError):
        SyncOrchestrator(FailingClient(), session_factory).run(
            resource="ItemOrganisationRltd", limit=1
        )
    with session_factory() as session:
        session.add(ItemAtcRltd(**orphan_item_atc("FAILED")))
        with pytest.raises(IntegrityError):
            session.commit()
