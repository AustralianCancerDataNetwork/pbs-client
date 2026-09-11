"""Thin Typer command line interface over the library layers."""

from __future__ import annotations

from collections import Counter
from typing import Any

import typer
from sqlalchemy.engine import Engine

from pbs_client.config import PBSSettings, get_pbs_context
from pbs_client.db import init_db, make_session_factory
from pbs_client.errors import PBSHTTPError, PBSInvalidResponseError, PBSSyncError, PBSTransportError
from pbs_client.http import DEFAULT_PAGE_SIZE, PBSClient
from pbs_client.sync import SyncOrchestrator, mirror_status

app = typer.Typer(help="Maintain a local offline mirror of the PBS Public Data API v3.")


def _status_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render a compact operational summary followed by grouped resource details."""

    counts = Counter(row["status"] for row in rows)
    complete = counts.get("complete", 0)
    total_rows = sum(int(row["rows"]) for row in rows)
    state_summary = " · ".join(
        f"{counts.get(status, 0)} {label.lower()}"
        for status, label in (
            ("complete", "complete"),
            ("in_progress", "in progress"),
            ("failed", "failed"),
            ("pending", "pending"),
        )
        if counts.get(status, 0)
    )
    lines = [
        f"PBS mirror: {complete}/{len(rows)} resources complete · {total_rows:,} rows",
        f"State: {state_summary}",
    ]
    attention = [
        row["resource"]
        for row in rows
        if row["status"] in {"failed", "in_progress"}
    ]
    if attention:
        lines.append(f"Attention: {', '.join(attention)}")

    headings = {
        "failed": "Failed",
        "in_progress": "In progress",
        "pending": "Pending",
        "complete": "Complete",
    }
    for status in ("failed", "in_progress", "pending", "complete"):
        group = [row for row in rows if row["status"] == status]
        if not group:
            continue
        lines.extend(["", f"{headings[status]} ({len(group)})"])
        for row in group:
            if status == "complete":
                detail = (
                    f"{int(row['rows']):,} rows · page {row['page']} · "
                    f"completed {_format_status_time(row['completed_at'])}"
                )
            elif status == "in_progress":
                detail = (
                    f"{int(row['rows']):,} rows · page {row['page']} · "
                    f"started {_format_status_time(row['started_at'])}"
                )
            elif status == "failed":
                error = str(row["last_error"] or "unknown error").splitlines()[0]
                detail = f"{int(row['rows']):,} rows · page {row['page']} · {error}"
            else:
                detail = "not started"
            lines.append(f"  {row['resource']:<30} {detail}")
    return lines


def _format_status_time(value: Any) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _runtime() -> tuple[PBSSettings, Engine, str]:
    """Resolve the shared oa-configurator config, engine, and database name."""

    config, database = get_pbs_context()
    return PBSSettings.from_config(config), database.create_engine(future=True), config.pbs_db


def _find_cause[Error: BaseException](
    error: BaseException, expected: type[Error]
) -> Error | None:
    """Find a cause of the requested type retained in a wrapped exception."""

    current: BaseException | None = error
    while current is not None:
        if isinstance(current, expected):
            return current
        current = current.__cause__
    return None


def _report_sync_failure(error: PBSSyncError) -> None:
    """Print an actionable, traceback-free message for a failed CLI sync."""

    resource = error.resource or "the current resource"
    transport = _find_cause(error, PBSTransportError)
    http_error = _find_cause(error, PBSHTTPError)
    invalid_response = _find_cause(error, PBSInvalidResponseError)
    typer.echo(f"PBS sync paused on {resource}.", err=True)
    if transport is not None and transport.timed_out:
        typer.echo(
            "The PBS API did not respond before the request timeout after "
            f"{transport.attempts} attempts.",
            err=True,
        )
        typer.echo(
            "Try a smaller page size if the response is large; completed "
            "resources are already saved.",
            err=True,
        )
        limit = " --limit 1000"
    elif http_error is not None and http_error.status_code == 429:
        typer.echo(str(error), err=True)
        typer.echo(
            "The PBS API rate limit was reached. Wait before retrying; committed "
            "pages and completed resources are already saved.",
            err=True,
        )
        limit = ""
    elif invalid_response is not None:
        typer.echo(str(error), err=True)
        typer.echo(
            "The PBS API returned an empty or non-JSON response; this can "
            "happen when a page is too large or the service returns an error page.",
            err=True,
        )
        typer.echo(
            "Completed resources and committed pages are already saved. "
            "Retry with a smaller page size.",
            err=True,
        )
        limit = " --limit 1000"
    else:
        typer.echo(str(error), err=True)
        typer.echo("Completed resources are already saved and can be resumed.", err=True)
        limit = ""
    typer.echo("Resume with:", err=True)
    typer.echo(
        f"  uv run pbs-client sync --resource {resource} --resume-only{limit}",
        err=True,
    )


@app.command("init-db")
def init_db_command() -> None:
    """Create the local schema without making any network request."""

    _, engine, database_name = _runtime()
    init_db(engine)
    typer.echo(f"Initialized PBS database {database_name!r}")


@app.command("sync")
def sync_command(
    resource: str | None = typer.Option(None, help="Only sync one resource, e.g. Item."),
    refresh: bool = typer.Option(
        True, "--refresh/--resume-only", help="Refresh completed resources."
    ),
    limit: int = typer.Option(DEFAULT_PAGE_SIZE, min=1, help="API page size."),
) -> None:
    """Synchronize all PBS resources, or one resource, into the local mirror."""

    settings, engine, _ = _runtime()
    init_db(engine)
    sessions = make_session_factory(engine)
    try:
        results = SyncOrchestrator(PBSClient(settings), sessions).run(
            resource=resource,
            limit=limit,
            refresh_completed=refresh,
        )
    except PBSSyncError as exc:
        _report_sync_failure(exc)
        raise typer.Exit(code=1) from None
    for result in results:
        typer.echo(
            f"{result.resource}: {result.status}; pages={result.pages}; "
            f"records={result.records_written}"
        )


@app.command()
def status() -> None:
    """Show checkpoint status and local row counts for every resource."""

    _, engine, _ = _runtime()
    init_db(engine)
    with make_session_factory(engine)() as session:
        for line in _status_lines(mirror_status(session)):
            typer.echo(line)


def main() -> None:
    app()
