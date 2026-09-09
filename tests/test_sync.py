from __future__ import annotations

from pbs_client.cli.main import _report_sync_failure
from pbs_client.db import MODEL_BY_NAME, SyncState
from pbs_client.errors import PBSSyncError, PBSTransportError
from pbs_client.http import Page
from pbs_client.sync import SyncOrchestrator


def schedule(code, effective_date):
    return {
        "schedule_code": code,
        "revision_number": 1,
        "start_tsp": "2026-01-01T00:00:00Z",
        "effective_date": effective_date,
        "effective_month": "January",
        "effective_year": 2026,
        "publication_status": "PUBLISHED",
    }


class FakeClient:
    def __init__(self, pages, fail=False):
        self.pages = pages
        self.fail = fail
        self.calls = []

    def iter_pages(self, endpoint, *, limit, start_page):
        self.calls.append((endpoint, start_page))
        for page in self.pages[start_page - 1 :]:
            yield page
            if self.fail:
                self.fail = False
                raise RuntimeError("interrupted")


def test_sync_is_idempotent_and_upserts(session_factory):
    page = Page("/schedules", 1, 100, [schedule(1, "2026-01-01")], {"total_records": 1}, [])
    client = FakeClient([page])
    orchestrator = SyncOrchestrator(client, session_factory)

    first = orchestrator.run(resource="Schedule", limit=100)
    second = orchestrator.run(resource="Schedule", limit=100)

    with session_factory() as session:
        assert session.query(MODEL_BY_NAME["Schedule"]).count() == 1
        assert session.get(SyncState, "Schedule").status == "complete"
    assert first[0].status == second[0].status == "complete"


def test_sync_resumes_after_a_committed_page(session_factory):
    pages = [
        Page(
            "/schedules", 1, 1, [schedule(1, "2026-01-01")], {"total_records": 2}, [{"rel": "next"}]
        ),
        Page("/schedules", 2, 1, [schedule(2, "2026-02-01")], {"total_records": 2}, []),
    ]
    interrupted = FakeClient(pages, fail=True)
    orchestrator = SyncOrchestrator(interrupted, session_factory)

    try:
        orchestrator.run(resource="Schedule", limit=1)
    except PBSSyncError:
        pass
    else:
        raise AssertionError("expected interruption")

    resumed = FakeClient(pages)
    result = SyncOrchestrator(resumed, session_factory).run(resource="Schedule", limit=1)

    with session_factory() as session:
        assert session.query(MODEL_BY_NAME["Schedule"]).count() == 2
        assert session.get(SyncState, "Schedule").status == "complete"
    assert resumed.calls == [("/schedules", 2)]
    assert result[0].records_written == 2


def test_cli_timeout_message_explains_how_to_resume(capsys):
    try:
        raise PBSTransportError(
            "https://example.test/restrictions?page=1", 4, TimeoutError("read timed out")
        )
    except PBSTransportError as transport_error:
        try:
            raise PBSSyncError("sync failed", resource="RestrictionText") from transport_error
        except PBSSyncError as sync_error:
            _report_sync_failure(sync_error)

    output = capsys.readouterr().err
    assert "PBS sync paused on RestrictionText" in output
    assert "did not respond before the request timeout" in output
    assert "--resume-only --limit 1000" in output
