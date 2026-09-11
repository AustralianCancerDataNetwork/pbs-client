from pathlib import Path

from oa_configurator import (
    ConnectionConfig,
    GenericDatabaseConfig,
    Resolver,
    StackConfig,
)

from pbs_client.config import MIN_RATE_LIMIT_SECONDS, PBSClientConfig, PBSSettings


def test_pbs_config_resolves_shared_generic_database(tmp_path: Path):
    stack = StackConfig.for_session(
        connections={
            "pbs_local": ConnectionConfig(
                dialect="sqlite",
                database_name=str(tmp_path / "pbs.db"),
            )
        },
        databases={
            "pbs_db": GenericDatabaseConfig(connection="pbs_local"),
        },
        tools={
            "pbs_client": {
                "pbs_db": "pbs_db",
                "subscription_key": "configured-key",
                "rate_limit_seconds": MIN_RATE_LIMIT_SECONDS,
            }
        },
    )

    config = Resolver(stack).resolve_package_config(PBSClientConfig)
    database = Resolver(stack).resolve_database(config.pbs_db)

    assert config.subscription_key == "configured-key"
    assert config.rate_limit_seconds == MIN_RATE_LIMIT_SECONDS
    assert database.name == "pbs_db"
    assert database.connection.url == f"sqlite:///{tmp_path / 'pbs.db'}"


def test_settings_can_be_built_from_package_config():
    config = PBSClientConfig(
        subscription_key="configured-key",
        base_url="https://example.test/",
        rate_limit_seconds=MIN_RATE_LIMIT_SECONDS,
    )

    settings = PBSSettings.from_config(config)

    assert settings.subscription_key == "configured-key"
    assert settings.base_url == "https://example.test"
    assert settings.rate_limit_seconds == MIN_RATE_LIMIT_SECONDS
