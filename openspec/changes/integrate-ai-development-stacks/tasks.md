# Tasks

## 1. Define and validate the catalog contracts

- [ ] 1.1 Add versioned JSON Schemas for the existing single-service preset format and the new bundle descriptor format; verify every current YAML preset and `services/index.json` entry validates against the schemas.
- [ ] 1.2 Implement a local catalog preflight command that checks schema validity, index-to-file parity, duplicate names, dependency cycles, supported platform metadata, and committed secret literals; verify it passes the current catalog and rejects fixtures for each invalid case.
- [ ] 1.3 Add a CI workflow that runs the static catalog preflight on proposed changes; verify invalid schema, index, dependency, platform, resource-limit, and secret fixtures fail the job without pulling images.
- [ ] 1.4 Document the bundle manifest fields, safety limits, platform and resource-limit declarations, and exact preflight command in the contribution guide; verify a contributor can validate a sample bundle using only the documented instructions.

## 2. Add Lerd runtime support for service bundles

- [ ] 2.1 Create and land the paired Lerd runtime change for the versioned bundle contract; verify a fixture bundle is discovered only by compatible Lerd versions and existing single-service catalog behavior still works.
- [ ] 2.2 Implement bundle component naming, internal service networking, loopback host publishing, durable state, readiness ordering, partial-failure reporting, grouped lifecycle operations, and optional per-component CPU/memory limits on supported runtime profiles; verify lifecycle behavior through CLI, UI, and MCP and verify unsupported limits are rejected before image pulls.
- [ ] 2.3 Add platform compatibility checks before image pulls and bundle-local secret handling; verify unsupported OS/architecture pairs are refused before download and no catalog or committed project file contains generated credentials.
- [ ] 2.4 Run the Lerd local preflight (`lerd-preflight`) and exercise a live bundle install/start/stop path; record the Lerd release or minimum version that supports this bundle schema.

## 3. Publish an Ollama-backed developer path

- [ ] 3.1 Add an Open WebUI service preset with a pinned reviewed image, persistent application data, an Ollama family dependency, and `OLLAMA_BASE_URL` wired to the in-network Lerd endpoint; verify it validates and its dependency resolves to the installed Ollama preset.
- [ ] 3.2 Verify Ollama model persistence and Open WebUI model discovery on a supported CPU-only Lerd host; record the image references, host profile, and observed results in the integration guide.

## 4. Add the Firecrawl bundle

- [ ] 4.1 Select one Firecrawl release and verify matching API, Playwright, Redis, RabbitMQ, and `nuq-postgres` images plus platform manifests against that release's upstream Compose configuration; record pinned tags or digests and supported platform pairs before writing the bundle descriptor.
- [ ] 4.2 Add the Firecrawl bundle descriptor with isolated dependencies, durable state, generated or operator-supplied secrets, local-only API publication, Ollama unset by default, and only those optional CPU/memory limits that the selected host/runtime profile can enforce; do not encode an unverified minimum resource recommendation. Verify the descriptor passes preflight and unsupported platform or resource settings are rejected before image pulls.
- [ ] 4.3 Run the bundle on a supported rootless-Podman host and exercise a real `POST /v2/scrape` request; verify the returned extraction includes Markdown and that a deliberately stopped required component is reported as not ready with its component name.

## 5. Document and review the integration

- [ ] 5.1 Update the catalog README with the Ollama/Open WebUI path, Firecrawl components and platform support, host versus in-container URLs, image/data expectations, and the unauthenticated-local-API boundary; verify each command and URL against the completed runtime.
- [ ] 5.2 Run the catalog preflight across every preset and bundle and review the rendered catalog metadata against the descriptors; record the exact command and result before opening a change.
