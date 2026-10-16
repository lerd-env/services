# Spec Delta

## Purpose

Local AI development services give Lerd projects discoverable, reproducible endpoints for local inference and web research, with setup guidance that distinguishes host access from container-network access.

## ADDED Requirements

### Requirement: AI development services are catalogued for Lerd projects
The service catalog SHALL expose local inference and web-research services as discoverable Lerd presets or bundles with their purpose, dependencies, endpoints, and persistence needs.

#### Scenario: User discovers the local AI path
- **WHEN** a user searches the service catalog for local inference or web research
- **THEN** Lerd presents the Ollama service, an Ollama-dependent web interface, and the Firecrawl bundle with their component requirements

#### Scenario: Ollama service remains independently usable
- **WHEN** a user installs Ollama without the web interface or Firecrawl
- **THEN** Lerd exposes its local API endpoint and retains model data across container recreation

### Requirement: Project connection settings match the caller network
Lerd SHALL provide project setup values and guidance that use service DNS names from a Lerd container and loopback host ports from a host process.

#### Scenario: Project runs in Lerd containers
- **WHEN** a Lerd-managed PHP or custom-container project connects to Ollama or Firecrawl
- **THEN** its generated or documented service URL uses the service's Lerd network hostname and container port

#### Scenario: Developer uses a host process
- **WHEN** a developer calls a published service from the host
- **THEN** Lerd documentation provides the corresponding loopback URL and does not direct the host process to a container-only DNS name

### Requirement: Open WebUI connects to the selected Ollama service
The Open WebUI preset SHALL depend on an installed Ollama service and persist its own application data independently.

#### Scenario: Open WebUI starts with Ollama available
- **WHEN** a user starts Open WebUI after installing Ollama
- **THEN** Open WebUI receives the selected Ollama service's internal URL and can list its available models

#### Scenario: Ollama is not installed
- **WHEN** a user attempts to install or start Open WebUI without a compatible Ollama service
- **THEN** Lerd identifies the missing dependency and the catalog path needed to satisfy it

### Requirement: Firecrawl runs as an isolated local bundle
The Firecrawl bundle SHALL include the pinned API and browser components plus its required queue, cache, and dedicated database dependencies, with no implicit reliance on a project's shared application database.

#### Scenario: Firecrawl bundle is installed
- **WHEN** a user installs the Firecrawl bundle
- **THEN** Lerd provisions and connects all required components, retains their declared state, and exposes the API only through a local endpoint by default

#### Scenario: Firecrawl API authentication is not enabled
- **WHEN** the selected upstream configuration does not enable API authentication
- **THEN** the service remains restricted to local access and Lerd warns against publishing it beyond the host

### Requirement: Firecrawl readiness is verified through a scrape
The Firecrawl integration SHALL distinguish container health from successful end-to-end scraping.

#### Scenario: Components are healthy but a scrape fails
- **WHEN** containers report healthy but a scrape request cannot complete
- **THEN** Lerd reports the integration as not ready and identifies the API, browser, queue, database, or outbound-network failure when available

#### Scenario: Scrape completes
- **WHEN** the configured Firecrawl smoke check submits a supported URL and receives a successful extraction response
- **THEN** Lerd reports the bundle as ready for project use

### Requirement: Ollama integration with Firecrawl is opt-in
The Firecrawl bundle SHALL leave optional model-provider settings unset unless the user explicitly configures an Ollama endpoint.

#### Scenario: No model endpoint is selected
- **WHEN** a user installs Firecrawl without configuring Ollama
- **THEN** Firecrawl starts with its documented non-Ollama baseline and makes no outbound model-provider call through Ollama

#### Scenario: User selects local Ollama
- **WHEN** a user configures Firecrawl to use an installed Ollama service
- **THEN** Lerd supplies the internal Ollama URL without requiring a hosted API credential
