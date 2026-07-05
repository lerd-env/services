# Lerd Service Store

> The community-driven store of service presets that powers
> [Lerd](https://lerd.sh) — add a database, cache, search engine,
> or admin dashboard by editing YAML, no binary release required.

[![Part of Lerd](https://img.shields.io/badge/part%20of-lerd-ff2d20)](https://lerd.sh)
[![Docs](https://img.shields.io/badge/docs-lerd.sh-blue)](https://lerd.sh/usage/service-presets)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Run `lerd service search`, pick something, `lerd service preset <name>` — and Lerd pulls the matching preset from this store, then knows exactly how to run it: which image and ports, how to wire your project's `.env`, which admin dashboard to embed, what it depends on, and which config files to mount for auto-login. Everything is a single YAML file. Add a service here and every Lerd install can use it within 24 hours, with no new Lerd release and no Go code.

That's the whole point: **Lerd ships only the default stack — MySQL, PostgreSQL, Redis, Meilisearch, RustFS, Mailpit — and every other service lives here.** MongoDB, MariaDB, phpMyAdmin, pgAdmin, Elasticsearch, RabbitMQ, and whatever you add next are all defined in this repo, not hardcoded in the binary.

## What a preset powers

A single `<name>.yaml` teaches Lerd to:

- 📦 **Run the container** — image, ports, volumes, and environment, wired into a rootless Podman quadlet
- 🌱 **Wire your `.env`** — inject the host, port, and credentials your framework expects, with auto-detection
- 🖥️ **Embed a dashboard** — phpMyAdmin, pgAdmin, RedisInsight and friends open inside the Lerd UI, already logged in
- 👪 **Group into families** — alternates and admin UIs discover every installed family member automatically
- 🔢 **Offer versions** — ship multiple selectable image tags; every member shares the family's canonical host port and Lerd shifts collisions for you
- 🔗 **Declare dependencies** — pull in the services a preset needs, started in order
- 📄 **Mount config files** — static files inline, or dynamic ones (like pgAdmin's discovered server list) via a built-in generator

All of it is data. None of it ships in the binary.

## Available services

**Databases**

| Service | What it is |
|---------|------------|
| `mariadb` | MariaDB, the MySQL-compatible server (multi-version) |
| `mongo` | MongoDB document database |
| `postgres-pgvector` | PostgreSQL + pgvector for vector search (multi-version) |
| `postgres-timescaledb` | PostgreSQL + TimescaleDB for time-series (multi-version) |

**Admin dashboards** — open inside the Lerd UI, auto-logged-in

| Service | For |
|---------|-----|
| `phpmyadmin` | every installed MySQL / MariaDB service |
| `pgadmin` | every installed PostgreSQL service |
| `mongo-express` | MongoDB |
| `redisinsight` | Redis |
| `elasticvue` | Elasticsearch |
| `typesense-dashboard` | Typesense |

**Search & analytics**

| Service | What it is |
|---------|------------|
| `elasticsearch` | Elasticsearch single-node engine |
| `opensearch` | OpenSearch single-node engine |
| `typesense` | Typesense typo-tolerant search |

**Cache, queues & messaging**

| Service | What it is |
|---------|------------|
| `valkey` | Valkey, the Redis-compatible cache (coexists with Redis) |
| `memcached` | Memcached in-memory cache |
| `rabbitmq` | RabbitMQ broker with management UI |
| `soketi` | Pusher-compatible WebSocket server |
| `beanstalkd` | Beanstalkd work queue |

**Testing & tooling**

| Service | What it is |
|---------|------------|
| `selenium` | Headless Chromium with a noVNC viewer for browser tests |
| `stripe-mock` | Stripe API mock server |
| `gotenberg` | Gotenberg API for PDF and document conversion |

Don't see what you need? [Add it](#contributing) — that's what this repo is for.

## Usage

You rarely touch the store directly: everything routes through the usual service commands.

```bash
lerd service search                  # list everything available
lerd service search search-engine    # search by name, description, or family
lerd service preset phpmyadmin        # install a preset (fetched on demand)
lerd service preset mariadb --version 11.8   # pick a version on multi-version presets
```

Installed presets are cached locally and auto-refresh every 24 hours, so improvements landed here reach existing installs without an update.

## Contributing

New services and version bumps are welcome — this store is only as good as the community around it.

1. Fork this repo
2. Add or update `services/<name>.yaml`
3. Add or update the matching entry in `services/index.json` (name, description, and optionally family, dashboard, depends_on)
4. Open a pull request

Keep images pinned to a specific tag or a `track_latest` family; avoid `:latest` for anything that stores data.

### Preset schema

Definitions live under `services/`: an `index.json` catalogue plus one `<name>.yaml` per preset. A minimal preset:

```yaml
name: my-service
image: docker.io/example/my-service:1
description: What it is
ports:
  - "8099:80"
```

Common fields build on that:

```yaml
family: my-family          # group alternates + dashboards for auto-discovery
versions:                  # multi-version family (all share the canonical port)
  - tag: "2"
    image: docker.io/example/my-service:2
    canonical: true
env_vars:                  # keys injected into the project .env
  - MY_HOST=lerd-{{name}}
dynamic_env:               # computed at install time (e.g. family discovery)
  MY_HOSTS: discover_family:my-family
depends_on:                # started first
  - mysql
dashboard: http://localhost:8099
files:                     # config-file mounts (static content, or a generator)
  - target: /etc/my-service/config
    content: |
      key = value
```

See the [service presets documentation](https://lerd.sh/usage/service-presets) for the full schema reference and every available field.

## License

MIT
