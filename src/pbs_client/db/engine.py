"""Database engine and schema helpers."""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from pbs_client.db.model import Base


def make_session_factory(engine: Engine):
    """Return a configured SQLAlchemy session factory."""

    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db(engine: Engine) -> None:
    """Create the complete local mirror schema if it does not exist."""

    Base.metadata.create_all(engine)
