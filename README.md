# lerd service presets

External service-preset store for [lerd](https://lerd.sh). Publishing a preset here makes it installable with `lerd service preset <name>` (and discoverable with `lerd service search`) without shipping a new lerd release.

The default service stack (mysql, redis, postgres, meilisearch, rustfs, mailpit) is built into lerd. Everything else, the opt-in add-ons, lives here.

## Layout

Flat repo, served over `raw.githubusercontent.com`:

- `index.json` — the catalogue lerd reads for `lerd service search`.
- `<name>.yaml` — one file per preset, fetched on install and cached under `~/.local/share/lerd/service-presets/`.

## index.json

```json
{
  "services": [
    { "name": "phpmyadmin", "description": "phpMyAdmin web UI for every installed lerd MySQL service", "depends_on": ["mysql"], "dashboard": "http://localhost:8080" }
  ]
}
```

Fields: `name` (required, matches `<name>.yaml`), `description`, `family`, `dashboard`, `depends_on`. Only what's needed to list and search; the full definition lives in the preset file.

## Preset schema

Each `<name>.yaml` is the same schema lerd uses internally. Minimum:

```yaml
name: my-service
image: docker.io/example/my-service:1
description: What it is
ports:
  - "8099:80"
```

Common fields: `family` (groups related services for dashboard discovery), `versions` (multi-version families; every member defaults to the family's canonical host port and lerd shifts later siblings off it), `env_vars` (project `.env` keys), `dynamic_env` (family-discovery values like `discover_family:mysql`), `depends_on`, `dashboard`, `data_dir`, `connection_url`, `files` (config-file mounts; static `content` inline, or a built-in `generator` for dynamic contents).

See the [service presets documentation](https://lerd.sh/usage/service-presets) for the full reference.

## Contributing

Add `<name>.yaml`, add the matching entry to `index.json`, open a PR. Keep images pinned to a specific tag or a `track_latest` family; avoid `:latest` for databases.
