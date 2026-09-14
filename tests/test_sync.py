from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module

import pytest
from typer.testing import CliRunner

from pbs_client.cli.main import _report_sync_failure, _status_lines
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


def report_wrapped_failure(error, resource, *, capsys):
    try:
        raise PBSSyncError("sync failed", resource=resource) from error
    except PBSSyncError as sync_error:
        _report_sync_failure(sync_error)
    return capsys.readouterr().err


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


def test_sync_fails_instead_of_completing_below_api_total(session_factory):
    page = Page(
        "/schedules",
        1,
        1,
        [schedule(1, "2026-01-01")],
        {"total_records": 2},
        [],
    )

    with pytest.raises(PBSSyncError, match="wrote 1 of the API-reported 2 records"):
        SyncOrchestrator(FakeClient([page]), session_factory).run(
            resource="Schedule", limit=1
        )

    with session_factory() as session:
        state = session.get(SyncState, "Schedule")
        assert state.status == "failed"
        assert state.records_written == 1
        assert state.metadata_json["total_records"] == 2
        assert state.completed_at is None


def test_sync_progress_tracks_page_totals(session_factory, monkeypatch):
    observed = []

    class RecordingProgress:
        def __init__(self, *_columns, **_options):
            self.total = None
            self.completed = 0
            observed.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def add_task(self, _description, *, total=None, completed=0):
            self.total = total
            self.completed = completed
            return 1

        def update(self, _task_id, *, total=None):
            if total is not None:
                self.total = total

        def advance(self, _task_id, amount):
            self.completed += amount

    sync_module = import_module("pbs_client.sync.orchestrator")
    monkeypatch.setattr(sync_module, "Progress", RecordingProgress)
    pages = [
        Page(
            "/schedules",
            1,
            2,
            [schedule(1, "2026-01-01"), schedule(2, "2026-01-01")],
            {"total_records": 3},
            [],
        ),
        Page(
            "/schedules",
            2,
            2,
            [schedule(3, "2026-01-01")],
            {"total_records": 3},
            [],
        ),
    ]

    SyncOrchestrator(FakeClient(pages), session_factory).run(
        resource="Schedule", limit=2
    )

    assert len(observed) == 1
    assert observed[0].total == 3
    assert observed[0].completed == 3


@pytest.mark.parametrize(
    ("resource", "records_written", "total_records", "exit_code"),
    [
        ("MarkupBand", 1748, 1748, 0),
        ("ItemDispensingRuleRltd", 56181, 501181, 1),
    ],
)
def test_verify_command_checks_written_count_not_table_rows(
    session_factory, monkeypatch, resource, records_written, total_records, exit_code
):
    endpoint = "/markup-bands" if resource == "MarkupBand" else "/item-dispensing-rule-relationships"
    with session_factory() as session:
        session.add(
            SyncState(
                resource=resource,
                endpoint=endpoint,
                status="complete",
                records_written=records_written,
                metadata_json={"total_records": total_records},
            )
        )
        session.commit()

    probe = session_factory()
    engine = probe.get_bind()
    probe.close()
    cli_main = import_module("pbs_client.cli.main")
    monkeypatch.setattr(cli_main, "_runtime", lambda: (None, engine, "test_db"))
    monkeypatch.setattr(
        cli_main,
        "init_db",
        lambda _: pytest.fail("verify must not mutate or initialize the mirror"),
    )

    result = CliRunner().invoke(cli_main.app, ["verify"])

    assert result.exit_code == exit_code
    if exit_code:
        assert "ItemDispensingRuleRltd" in result.output
        assert "56,181/501,181" in result.output
    else:
        assert "verification passed" in result.output


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


def test_sync_restarts_when_page_size_changes(session_factory):
    pages = [
        Page("/schedules", 1, 1, [schedule(1, "2026-01-01")], {"total_records": 2}, [{"rel": "next"}]),
        Page("/schedules", 2, 1, [schedule(2, "2026-02-01")], {"total_records": 2}, []),
    ]
    interrupted = FakeClient(pages, fail=True)
    try:
        SyncOrchestrator(interrupted, session_factory).run(resource="Schedule", limit=1)
    except PBSSyncError:
        pass

    resumed = FakeClient(pages)
    result = SyncOrchestrator(resumed, session_factory).run(resource="Schedule", limit=2)

    with session_factory() as session:
        assert session.query(MODEL_BY_NAME["Schedule"]).count() == 2
    assert resumed.calls == [("/schedules", 1)]
    assert result[0].records_written == 2


def test_refresh_retains_rows_missing_from_the_latest_page(session_factory):
    first = Page(
        "/schedules",
        1,
        100,
        [schedule(1, "2026-01-01"), schedule(2, "2026-02-01")],
        {"total_records": 2},
        [],
    )
    SyncOrchestrator(FakeClient([first]), session_factory).run(resource="Schedule", limit=100)

    second = Page("/schedules", 1, 100, [schedule(1, "2026-01-01")], {"total_records": 1}, [])
    SyncOrchestrator(FakeClient([second]), session_factory).run(resource="Schedule", limit=100)

    with session_factory() as session:
        assert session.query(MODEL_BY_NAME["Schedule"]).count() == 2


def test_failed_refresh_clears_previous_completion_time(session_factory):
    page = Page("/schedules", 1, 100, [schedule(1, "2026-01-01")], {"total_records": 1}, [])
    SyncOrchestrator(FakeClient([page]), session_factory).run(resource="Schedule", limit=100)

    failing = FakeClient([page], fail=True)
    try:
        SyncOrchestrator(failing, session_factory).run(resource="Schedule", limit=100)
    except PBSSyncError:
        pass

    with session_factory() as session:
        state = session.get(SyncState, "Schedule")
        assert state.status == "failed"
        assert state.completed_at is None


def test_cli_timeout_message_explains_how_to_resume(capsys):
    transport_error = PBSTransportError(
        "https://example.test/restrictions?page=1", 4, TimeoutError("read timed out")
    )
    output = report_wrapped_failure(transport_error, "RestrictionText", capsys=capsys)
    assert "PBS sync paused on RestrictionText" in output
    assert "did not respond before the request timeout" in output
    assert "--resume-only --limit 1000" in output


def test_cli_invalid_json_message_explains_how_to_reduce_page_size(capsys):
    from pbs_client.errors import PBSInvalidResponseError

    api_error = PBSInvalidResponseError(
        "PBS endpoint /item-dispensing-rule-relationships returned invalid JSON"
    )
    output = report_wrapped_failure(api_error, "ItemDispensingRuleRltd", capsys=capsys)
    assert "empty or non-JSON response" in output
    assert "--resume-only --limit 1000" in output


def test_status_output_summarises_and_groups_resources():
    lines = _status_lines(
        [
            {
                "resource": "Schedule",
                "status": "complete",
                "rows": 13,
                "page": 1,
                "started_at": None,
                "completed_at": datetime(2026, 9, 10, 0, 26, tzinfo=UTC),
                "last_error": None,
            },
            {
                "resource": "MarkupBand",
                "status": "in_progress",
                "rows": 0,
                "page": 0,
                "started_at": datetime(2026, 9, 11, 3, 5, tzinfo=UTC),
                "completed_at": None,
                "last_error": None,
            },
            {
                "resource": "Prescriber",
                "status": "pending",
                "rows": 0,
                "page": 0,
                "started_at": None,
                "completed_at": None,
                "last_error": None,
            },
        ]
    )

    output = "\n".join(lines)
    assert "PBS mirror: 1/3 resources complete · 13 rows" in output
    assert "Attention: MarkupBand" in output
    assert "In progress (1)" in output
    assert "Complete (1)" in output
    assert "Pending (1)" in output
