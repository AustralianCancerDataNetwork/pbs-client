"""Database engine and schema helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from pbs_client.db.model import Base


def database_url(path_or_url: str | Path) -> str:
    """Return a SQLAlchemy URL for a filesystem path or an explicit URL."""

    value = str(path_or_url)
    if "://" in value:
        return value
    return f"sqlite:///{Path(value).expanduser()}"


def make_engine(path_or_url: str | Path = "pbs_client.db") -> Engine:
    """Construct an engine without connecting or making network requests."""

    return create_engine(database_url(path_or_url), future=True)


def make_session_factory(engine: Engine):
    """Return a configured SQLAlchemy session factory."""

    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db(engine: Engine) -> None:
    """Create the complete local mirror schema if it does not exist."""

    Base.metadata.create_all(engine)
