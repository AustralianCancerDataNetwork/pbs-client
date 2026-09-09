from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pbs_client.db import init_db


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"

