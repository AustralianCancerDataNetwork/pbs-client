"""PBS client settings and oa-configurator integration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, ClassVar

from oa_configurator import (
    GenericDatabaseConfig,
    PackageConfigBase,
    RefTo,
    ResolvedDatabase,
    Resolver,
    Sensitive,
    load_stack_config,
)
from pydantic import Field


DEFAULT_BASE_URL = "https://data-api.health.gov.au/pbs/api/v3"
DEFAULT_PUBLIC_KEY = "2384af7c667342ceb5a736fe29f1dc6b"
DEFAULT_RATE_LIMIT_SECONDS = 20.0


class PBSClientConfig(PackageConfigBase):
    """Typed ``[tools.pbs_client]`` configuration for the PBS mirror.

    The database is a named generic database rather than a package-local path,
    so another package—eventually Groundworkers—can resolve and use the same
    persisted PBS mirror through oa-configurator.
    """

    tool_name: ClassVar[str] = "pbs_client"

    pbs_db: Annotated[str, RefTo(GenericDatabaseConfig)] = Field(
        default="pbs_db",
        description="Name of the generic database that stores the PBS mirror.",
    )
    subscription_key: Annotated[str, Sensitive()] = Field(
        default=DEFAULT_PUBLIC_KEY,
        description="PBS Public Data API subscription key.",
    )
    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        description="PBS Public Data API v3 base URL.",
    )
    rate_limit_seconds: float = Field(
        default=DEFAULT_RATE_LIMIT_SECONDS,
        gt=0,
        description="Minimum delay between PBS API requests in seconds.",
    )


def get_pbs_context() -> tuple[PBSClientConfig, ResolvedDatabase]:
    """Load the configured PBS client and resolve its mirror database.

    Raises
    ------
    RuntimeError
        If the shared oa-configurator stack file has not been created yet.
    """

    try:
        stack = load_stack_config()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "No pbs-client configuration found. "
            "Run `omop-config configure pbs_client` to set it up."
        ) from exc
    resolver = Resolver(stack)
    config = resolver.resolve_package_config(PBSClientConfig)
    database = resolver.resolve_database(config.pbs_db)
    return config, database


@dataclass(frozen=True, slots=True)
class PBSSettings:
    """Configuration used by the HTTP, database, and CLI layers."""

    subscription_key: str = DEFAULT_PUBLIC_KEY
    db_path: Path = Path("pbs_client.db")
    base_url: str = DEFAULT_BASE_URL
    rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS

    @classmethod
    def from_config(cls, config: PBSClientConfig) -> PBSSettings:
        """Build HTTP settings from the resolved package configuration."""

        return cls(
            subscription_key=config.subscription_key,
            base_url=config.base_url.rstrip("/"),
            rate_limit_seconds=config.rate_limit_seconds,
        )

    @classmethod
    def from_env(cls) -> PBSSettings:
        """Build settings from the documented ``PBS_CLIENT_*`` variables."""

        rate = os.getenv("PBS_CLIENT_RATE_LIMIT_SECONDS")
        return cls(
            subscription_key=os.getenv("PBS_CLIENT_SUBSCRIPTION_KEY", DEFAULT_PUBLIC_KEY),
            db_path=Path(os.getenv("PBS_CLIENT_DB_PATH", "./pbs_client.db")),
            base_url=os.getenv("PBS_CLIENT_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            rate_limit_seconds=float(rate) if rate else DEFAULT_RATE_LIMIT_SECONDS,
        )
