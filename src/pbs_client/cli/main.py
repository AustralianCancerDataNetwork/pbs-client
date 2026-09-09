"""Thin Typer command line interface over the library layers."""

from __future__ import annotations

import typer
from sqlalchemy.engine import Engine

from pbs_client.config import PBSSettings, get_pbs_context
from pbs_client.db import init_db, make_session_factory
from pbs_client.errors import PBSSyncError, PBSTransportError
from pbs_client.http import PBSClient
from pbs_client.sync import SyncOrchestrator, mirror_status

app = typer.Typer(help="Maintain a local offline mirror of the PBS Public Data API v3.")


def _runtime() -> tuple[PBSSettings, Engine, str]:
    """Resolve the shared oa-configurator config, engine, and database name."""

    config, database = get_pbs_context()
    return PBSSettings.from_config(config), database.create_engine(future=True), config.pbs_db


def _find_transport_error(error: BaseException) -> PBSTransportError | None:
    """Find a transport failure retained in a wrapped sync exception."""

    current: BaseException | None = error
    while current is not None:
        if isinstance(current, PBSTransportError):
            return current
        current = current.__cause__
    return None


def _report_sync_failure(error: PBSSyncError) -> None:
    """Print an actionable, traceback-free message for a failed CLI sync."""

    resource = error.resource or "the current resource"
    transport = _find_transport_error(error)
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
    limit: int = typer.Option(100_000, min=1, help="API page size."),
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
        for row in mirror_status(session):
            completed = row["completed_at"].isoformat() if row["completed_at"] else "-"
            typer.echo(
                f"{row['resource']}: {row['status']}; rows={row['rows']}; "
                f"page={row['page']}; completed={completed}"
            )


def main() -> None:
    app()
