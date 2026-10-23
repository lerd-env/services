# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. The current store has one YAML preset per service and one `services/index.json` catalogue; the Ollama preset shows the existing single-container path. The checkout has no `schema/` or validator. Lerd currently downloads and operates individual service presets, while Firecrawl’s documented self-host configuration is a multi-container Compose application.

The new contract must be additive so existing Lerd releases can keep reading `services/index.json` and existing single-image presets unchanged. The runtime half belongs in the Lerd repository; this repository owns the public bundle format, example data, validation, and contribution documentation.

## Goals / Non-Goals

**Goals:**

- Define a small, versioned contract for catalog bundles that Lerd can safely translate into its existing rootless service lifecycle.
- Prove the contract with Open WebUI + Ollama and a Firecrawl deployment whose API, browser, queue, cache, and database are represented explicitly.
- Validate catalog data statically and provide an end-to-end Firecrawl readiness check on a supported Lerd host.

**Non-Goals:**

- Accept arbitrary Docker Compose files, build images from source, or pass arbitrary shell commands to containers.
- Promise GPU acceleration, production availability, public Internet exposure, or a universal resource floor.
- Package Context.dev credentials or implement a self-modifying agent harness.

## Decisions

### Keep the existing service index stable and add a separate bundle registry

Add `bundles/index.json` and `bundles/<bundle-name>.yaml`, plus JSON Schemas under `schema/`. The bundle index contains only discovery metadata and a descriptor path; descriptors use a declared schema version. Lerd versions that do not understand bundles continue using `services/index.json` unchanged. New Lerd versions fetch the bundle registry only when their runtime supports that schema version.

**Alternative considered:** Put bundle entries into the existing `services/index.json`. That makes older clients depend on undocumented unknown-field behavior and risks changing a stable service-only payload. A separate registry gives the runtime an explicit capability boundary.

### Use a constrained manifest, not Docker Compose passthrough

The manifest describes a named set of image components, image references and supported OS/architecture pairs, internal ports, host-published ports, environment mappings, persistent state, dependencies/readiness, and supported resource/security settings. Optional per-component CPU and memory limits are accepted only on host/runtime profiles where Lerd can enforce them; omitted limits leave runtime defaults in place, and limits are not a resource-sizing recommendation. It has no arbitrary host mounts, privileged mode, device passthrough, or free-form shell hooks. Lerd validates the descriptor and current-host compatibility before pulling images and rejects unsupported fields or dependency cycles.

**Alternative considered:** Ship Firecrawl’s upstream Compose file and ask users to run it. That bypasses Lerd’s lifecycle, service UI, rootless systemd ownership, and project endpoint wiring, and it makes the catalog claim less useful than a Lerd service preset.

### Translate a bundle into Lerd-managed component units

`lerd service preset firecrawl` creates one unit per component with stable bundle-scoped service names on Lerd’s service network. Internal dependencies are reachable by those names; only declared bundle entrypoints are host-published, bound to loopback by default. A bundle-level operation presents one install/start/stop/update/remove control while retaining component logs, health, image version, and failure detail.

Data directories and per-bundle runtime state are separate from image versions. Updates replace image references while preserving declared data. A failed update reports the completed and failed components and retains data for retry or rollback; stateful migrations are not claimed to be transactionally reversible.

**Alternative considered:** Use a separate private network for every bundle. Lerd-managed PHP and custom-container projects need to reach the service endpoints on Lerd’s shared network; a private network would require a second routing/proxy layer. The first version therefore keeps internal component ports unpublished and scopes hostnames by bundle, while exposing only explicitly declared entrypoints on loopback.

### Generate bundle-local credentials and keep unauthenticated services local

Any credential required for internal service-to-service communication is generated at install time or requested from the operator, then persisted in user-only local Lerd state with restrictive permissions. It is never stored in the catalog, `services/index.json`, a committed `.lerd.yaml`, or project-facing endpoint values. Firecrawl’s unauthenticated local API is published only on loopback by default; broader exposure remains a separate operator decision with an explicit supported authentication and network policy.

**Alternative considered:** Reuse Lerd’s shared PostgreSQL, Redis, or RabbitMQ presets for Firecrawl. The inspected Firecrawl Compose configuration uses a Firecrawl-specific Postgres image and its own queue/cache services; sharing Lerd’s app database would weaken isolation and may omit required Postgres behavior.

### Build the AI path from existing services and keep model providers optional

Keep the current Ollama preset as the local inference endpoint, add Open WebUI as a dependent single-container preset with its own persistent state, and add Firecrawl as a bundle with a dedicated Postgres, Redis, RabbitMQ, and Playwright component. Firecrawl’s optional `OLLAMA_BASE_URL` is unset unless the user selects a Lerd-managed Ollama endpoint. Project-facing values use Lerd DNS names from containers; documentation gives loopback host URLs for host processes.

Images are pinned to a reviewed release tag or digest. Firecrawl’s inspected Compose file builds the API and Playwright service from source by default even though GHCR packages exist. Implementation must verify version alignment, availability, and supported architectures for the API, Playwright, and `nuq-postgres` images before marking the bundle installable. If a compatible image set is unavailable for a host profile, mark that profile unsupported rather than building arbitrary project source during service installation.

### Separate static catalog checks from runtime acceptance

The store provides a documented local preflight command for schema validation, index-to-file parity, duplicate-name and dependency-graph checks, platform metadata, optional resource-limit compatibility, and secret-literal checks. CI runs the same static preflight so catalog errors block review consistently. Before Firecrawl is published, a supported rootless-Podman integration run verifies bundle lifecycle and a real Firecrawl scrape. Lerd runtime changes also pass the existing `lerd-preflight` sequence, including install and a live smoke check of the affected service surface.

**Alternative considered:** Treat schema validation or container liveness as complete verification. The former cannot catch registry/runtime incompatibility; the latter does not establish that Firecrawl can scrape through its browser, queue, database, and outbound network.

## Risks / Trade-offs

- **Risk:** A bundle can fail after only some containers start. → **Mitigation:** Track member state, stop dependent members, preserve state, and provide retry/rollback detail.
- **Risk:** Upstream image or environment contracts drift. → **Mitigation:** Pin reviewed references, validate the selected release, and run the scrape smoke after updates.
- **Risk:** One bundle consumes substantial disk, memory, CPU, and outbound bandwidth. → **Mitigation:** Show components and image references before install, keep Ollama optional, do not claim minimum sizing, and use Lerd’s existing image-size disclosure where available.
- **Risk:** Firecrawl’s API is unauthenticated in its documented local baseline. → **Mitigation:** Loopback-only host binding by default and explicit warnings before any wider exposure.
- **Risk:** The catalog contract and Lerd runtime ship out of order. → **Mitigation:** Keep the separate registry undiscoverable to unsupported runtime versions and publish Firecrawl only after the Lerd companion change lands.

## Migration Plan

1. Land the bundle schema and validator in this repository without changing `services/index.json` or existing preset behavior.
2. Land the Lerd runtime companion behind bundle-schema support, then validate install/start/update/stop/remove and local endpoint wiring with a small fixture bundle.
3. Add Open WebUI and the Firecrawl bundle only after compatible images and local-only exposure are verified; run the actual scrape path.
4. Document `lerd service preset`, project environment setup, host/container URLs, and the Lerd preflight evidence required for future updates.

Rollback disables bundle-registry discovery in Lerd while leaving existing single-service presets intact. Removing an installed bundle follows Lerd’s normal data-retention choice; no rollback step deletes persistent state implicitly.
