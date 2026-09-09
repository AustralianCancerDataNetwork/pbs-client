# pbs-client

`pbs-client` is an offline-first Python client and local SQLite mirror for the Australian PBS Public Data API v3. It mirrors all API resources, retains schedule history locally, and exposes small read helpers for item, restriction/indication, and ATC lookups.

## Quick start

```shell
uv sync --extra dev
uv run omop-config configure pbs_client
uv run pbs-client init-db
uv run pbs-client sync
```

The package registers `PBSClientConfig` with `oa-configurator` under the
`pbs_client` tool name. The configuration wizard creates a `[tools.pbs_client]`
section and a named generic database entry (`pbs_db`) that can be shared with
downstream packages such as Groundworkers.

For a non-interactive local SQLite setup, the relevant stack configuration is:

```toml
[connections.pbs_local]
dialect = "sqlite"
database_name = "/absolute/path/to/pbs_client.db"

[databases.pbs_db]
kind = "generic"
connection = "pbs_local"

[tools.pbs_client]
pbs_db = "pbs_db"
subscription_key = "your-subscription-key"
```

Set `OA_CONFIG_PATH` before invoking the commands when using a config file
outside `~/.config/omop/config.toml`.

The public API is deliberately rate limited to one request per twenty seconds. The client enforces that interval process-wide, including retries and page continuations. Tests use local fixtures and never call the API.

All configuration — the subscription key, base URL, rate limit, and the
shared mirror database — is read from `oa-configurator`. There is no
environment-variable or CLI-flag fallback; run `uv run omop-config configure
pbs_client` before using the library or CLI.
