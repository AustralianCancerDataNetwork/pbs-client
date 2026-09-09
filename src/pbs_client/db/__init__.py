"""Local SQLAlchemy mirror for PBS API resources."""

from pbs_client.db.engine import database_url, init_db, make_engine, make_session_factory
from pbs_client.db.model import Base
from pbs_client.db.schema import (
    RESOURCE_BY_ENDPOINT,
    RESOURCE_BY_NAME,
    RESOURCE_SPECS,
    SYNC_ORDER,
)
from pbs_client.db.state import SyncState

MODEL_BY_NAME = {spec.name: spec.model for spec in RESOURCE_SPECS}

__all__ = [
    "MODEL_BY_NAME",
    "RESOURCE_BY_ENDPOINT",
    "RESOURCE_BY_NAME",
    "RESOURCE_SPECS",
    "SYNC_ORDER",
    "Base",
    "SyncState",
    "database_url",
    "init_db",
    "make_engine",
    "make_session_factory",
]
