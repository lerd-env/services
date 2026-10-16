# Proposal

## Why

Lerd’s external catalog makes single-container services easy to add, and this store already has an Ollama preset, but it cannot describe a complete developer stack such as self-hosted Firecrawl. Firecrawl’s published deployment needs multiple cooperating containers, persistent state, configuration, and startup checks; a catalog-only preset would imply support that the current contract cannot provide.

This change defines a Lerd-consumable service-bundle contract and uses it to connect local inference and web research to ordinary project setup. It also adds a store-owned validation gate so presets and bundles are checked before publication.

## What Changes

- Add a versioned bundle format for grouping pinned container images, dependencies, ports, durable data, health/readiness checks, generated or supplied secrets, and project-facing environment values under one installable Lerd service.
- Require Lerd to install, start, inspect, update, and remove a bundle as one unit while preserving data and reporting partial failures. Bundle members must have an internal network, explicit supported-platform metadata, and a host-facing API that remains local by default.
- Publish an AI development path that builds on the existing Ollama preset, adds Open WebUI as a dependent dashboard, and offers Firecrawl as a bundle with its own API, browser service, queue, cache, and Firecrawl-specific Postgres image. Ollama remains optional for Firecrawl and is configured only when selected.
- Document the app-facing connection path for Lerd projects, including the container-network URL and host URL, and show the `lerd env` / setup workflow without placing credentials in committed presets.
- Add schemas and a preflight validator for preset and bundle files, catalog/index consistency, dependency graphs, image references, platform compatibility, and secret hygiene; run the static preflight locally and in CI. Add an integration smoke check for a small bundle and the Firecrawl scrape path.
- Pair Lerd runtime work with its existing local preflight gate (`lerd-preflight`) and update the Lerd development guidance (`lerd-dev`) for bundle setup, endpoint wiring, and verification.

## Capabilities

### New Capabilities

- `service-bundles`: declarative, lifecycle-managed groups of service containers that Lerd can install and operate as one unit.
- `local-ai-development`: curated local inference and web-research services with clear project connection settings and verified readiness.

### Modified Capabilities

None. This repository currently has no published OpenSpec capability specs.

## Impact

The service catalog (`services/index.json` and `services/*.yaml`), a new `bundles/` directory, a new `schema/` directory, validation tooling, a CI workflow, and documentation will change here. A companion change in the Lerd runtime must consume bundle descriptors and provide grouped lifecycle, networking, configuration, resource-limit, and readiness behavior before a bundle is advertised as installable. The Lerd dev workflow should document app configuration; the Lerd preflight should exercise the new runtime surface. No runtime implementation is included in this repository proposal.

## Deferred ideas

- A broad AI lab catalog (LiteLLM, Langfuse, vector stores, workflow builders, and additional crawlers) until the bundle contract has one working, maintained example.
- GPU passthrough, performance promises, and hardware-specific model profiles; support varies by host, rootless container runtime, and device setup.
- Context.dev as a container preset: it is a hosted API integration and should remain an optional client-side provider with operator-managed credentials.
- Self-modifying agent harnesses and their evaluation loops: those need their own evaluator, sandbox, and acceptance controls and are outside a service catalog’s responsibility.

## Assumptions

- Lerd will accept a paired runtime change for the proposed bundle contract; this store alone cannot make a multi-container bundle run.
- The first Firecrawl bundle targets its documented local Docker Compose topology and a release-pinned API/browser image set. The exact image availability and configuration will be rechecked against the selected upstream release during implementation.
- The initial Ollama path is CPU-capable and local. GPU access is not implied by an Ollama container image.
- Per-component CPU and memory limits are optional operator controls only on host/runtime profiles where Lerd can enforce them. They are not a sizing recommendation or a guarantee of the resources Firecrawl needs.
- Presets and bundles must never embed hosted API credentials. Any required Firecrawl secret is generated or supplied through Lerd’s local secret handling.

## Evidence

- The current store README describes service presets as image, ports, environment, data, and dependency declarations, and `services/ollama.yaml` already supplies a local endpoint.
- Firecrawl’s [self-hosting guide](https://docs.firecrawl.dev/contributing/self-host) documents a Compose deployment; its [v2.11.162 Compose file](https://raw.githubusercontent.com/firecrawl/firecrawl/v2.11.162/docker-compose.yaml) includes API, Playwright, Redis, RabbitMQ, and a Firecrawl-specific Postgres image. Public GHCR packages exist for the API and Playwright images, but the Compose file builds them from source by default; exact release compatibility and architecture support remain to be checked. The guide warns that a successful heartbeat does not verify dependencies or an actual scrape, and that its baseline disables API authentication.
- Ollama’s [Docker guide](https://docs.ollama.com/docker) documents a persistent `/root/.ollama` volume and a CPU-only baseline; its GPU instructions require additional host setup.
- Open WebUI documents [Ollama endpoint configuration](https://docs.openwebui.com/reference/env-configuration/) through `OLLAMA_BASE_URL` and its [quick start](https://docs.openwebui.com/getting-started/quick-start/).
- Lerd’s [service preset guide](https://lerd.sh/usage/service-presets) documents existing preset, dependency, family, and environment-wiring behavior. The current checkout has no `schema/` directory or automated validation files despite the repository’s `AGENTS.md` requiring preset validation against `schema/`.
