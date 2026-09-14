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
    connection.  SQLite uses pool checkout/checkin listeners; Postgres uses
    orm_loader's engine-scoped replica role and disposes the pool afterwards so
    no connection carrying the disabled role can be reused.
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

    def disable_on_pool_event(dbapi_connection, *_args) -> None:
        _set_sqlite_foreign_keys(dbapi_connection, False)

    def enable_on_checkin(dbapi_connection, *_args) -> None:
        if dbapi_connection is not None:
            _set_sqlite_foreign_keys(dbapi_connection, True)

    event.listen(engine, "connect", disable_on_pool_event)
    event.listen(engine, "checkout", disable_on_pool_event)
    event.listen(engine, "checkin", enable_on_checkin)
    try:
        yield
    finally:
        event.remove(engine, "connect", disable_on_pool_event)
        event.remove(engine, "checkout", disable_on_pool_event)
        try:
            with engine.connect() as connection:
                state = _set_sqlite_foreign_keys(
                    connection.connection.driver_connection,
                    True,
                )
                if state != 1:
                    raise RuntimeError("Failed to restore SQLite foreign-key enforcement")
        finally:
            event.remove(engine, "checkin", enable_on_checkin)


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
