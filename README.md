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
outside `~/.config/omop/config.toml`. The legacy `--db-path` option remains
available for local one-off runs and uses the `PBS_CLIENT_*` environment
variables for API settings.

The public API is deliberately rate limited to one request per twenty seconds. The client enforces that interval process-wide, including retries and page continuations. Tests use local fixtures and never call the API.

Configuration is normally read from `oa-configurator`. Direct library use still
supports `PBS_CLIENT_SUBSCRIPTION_KEY`, `PBS_CLIENT_DB_PATH`,
`PBS_CLIENT_BASE_URL`, and `PBS_CLIENT_RATE_LIMIT_SECONDS`. The database
defaults to `./pbs_client.db` only for that legacy environment-variable path.
