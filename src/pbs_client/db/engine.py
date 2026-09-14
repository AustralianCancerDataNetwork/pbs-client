"""Database engine and schema helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from orm_loader.backends.resolve import resolve_backend
from orm_loader.helpers.bulk import engine_with_replica_role
from sqlalchemy import Engine, event
from sqlalchemy.orm import sessionmaker

from pbs_client.db.model import Base


def _set_sqlite_foreign_keys(dbapi_connection, enabled: bool) -> int:
    """Set this connection's FK flag outside any SQLite transaction."""

    autocommit = dbapi_connection.autocommit
    dbapi_connection.rollback()
    dbapi_connection.autocommit = True
    try:
        value = "ON" if enabled else "OFF"
        dbapi_connection.execute(f"PRAGMA foreign_keys = {value}").close()
        cursor = dbapi_connection.execute("PRAGMA foreign_keys")
        try:
            return cursor.fetchone()[0]
        finally:
            cursor.close()
    finally:
        dbapi_connection.autocommit = autocommit


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    _set_sqlite_foreign_keys(dbapi_connection, True)


@contextmanager
def fk_checks_disabled_for_refresh(engine: Engine) -> Iterator[None]:
    """Disable foreign-key checks across all page sessions in one refresh.

    The orchestrator commits each API page in a fresh session, so a session
    scoped PRAGMA/replication-role change would only affect one arbitrary pool
    connection. SQLite disables checks on checkout and restores them after the
    refresh; Postgres disposes the pool so disabled replica connections cannot
    be reused.
    """

    backend = resolve_backend(engine)
    if backend.name == "postgres":
        engine.dispose()
        try:
            with engine_with_replica_role(engine):
                yield
        finally:
            engine.dispose()
        return

    if backend.name != "sqlite":
        raise NotImplementedError(f"Unsupported database backend for PBS refresh: {backend.name}")

    def disable_on_checkout(dbapi_connection, *_args) -> None:
        cursor = dbapi_connection.execute("PRAGMA foreign_keys")
        try:
            if cursor.fetchone()[0] != 0:
                _set_sqlite_foreign_keys(dbapi_connection, False)
        finally:
            cursor.close()

    event.listen(engine, "checkout", disable_on_checkout)
    try:
        yield
    finally:
        event.remove(engine, "checkout", disable_on_checkout)
        database = engine.url.database
        in_memory = (
            database in (None, "", ":memory:", "file::memory:")
            or engine.url.query.get("mode") == "memory"
        )
        if not in_memory:
            # File-backed pool connections may still have FK checks disabled.
            engine.dispose()
        with engine.connect() as connection:
            state = _set_sqlite_foreign_keys(
                connection.connection.driver_connection,
                True,
            )
            if state != 1:
                raise RuntimeError("Failed to restore SQLite foreign-key enforcement")


def make_session_factory(engine: Engine):
    """Return a configured SQLAlchemy session factory."""

    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db(engine: Engine) -> None:
    """Create the complete local mirror schema if it does not exist."""

    if engine.dialect.name == "sqlite":
        if not event.contains(engine, "connect", _enable_sqlite_foreign_keys):
            event.listen(engine, "connect", _enable_sqlite_foreign_keys)
        with engine.connect() as connection:
            _set_sqlite_foreign_keys(connection.connection.driver_connection, True)
    Base.metadata.create_all(engine)
