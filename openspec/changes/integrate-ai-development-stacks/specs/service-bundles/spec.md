# Spec Delta

## Purpose

Service bundles let Lerd users install and operate a group of cooperating containers as one catalog choice, with clear ownership of dependencies, state, configuration, and failures.

## ADDED Requirements

### Requirement: Bundle descriptors are validated before installation
The catalog SHALL accept a bundle only when its supported schema version, component names, image references, dependency graph, and required configuration are valid.

#### Scenario: Valid bundle is discoverable
- **WHEN** a catalog bundle passes schema and dependency validation
- **THEN** Lerd can present it as one installable catalog choice with its components and host endpoints visible

#### Scenario: Invalid dependency graph is rejected
- **WHEN** a bundle has a missing component reference, duplicate component name, unsupported schema version, or dependency cycle
- **THEN** validation rejects it and identifies the bundle and invalid field or relationship

### Requirement: A bundle has one user-visible lifecycle
Lerd SHALL install, start, inspect, update, stop, and remove every component through the owning bundle while reporting component-level state and failures.

#### Scenario: Bundle starts in dependency order
- **WHEN** a user starts an installed bundle
- **THEN** Lerd starts dependencies before dependants and reports the state of each component under the bundle

#### Scenario: A component fails during startup
- **WHEN** a required component fails to start or become ready
- **THEN** Lerd reports the failing component and reason, stops dependants that cannot operate, and leaves the bundle recoverable through its lifecycle commands

### Requirement: Bundle state and network access are bounded
Each bundle SHALL define component state, internal connectivity, host-published endpoints, and secret inputs explicitly; catalog defaults MUST NOT publish an unauthenticated API beyond the local machine.

#### Scenario: State survives a container replacement
- **WHEN** a component image is updated or its container is recreated
- **THEN** its declared persistent state remains attached to that component

#### Scenario: Secret input is supplied safely
- **WHEN** a bundle needs a credential
- **THEN** Lerd obtains it from local secret handling or an operator-supplied value, and catalog data contains no reusable secret literal

#### Scenario: Local-only endpoint is published
- **WHEN** a bundle exposes a host port without an explicit operator request for broader access
- **THEN** Lerd binds the endpoint to loopback and documents its in-network address separately

### Requirement: Bundle platform compatibility is explicit
Each bundle SHALL declare the host platforms and architectures supported by all required components, and Lerd MUST reject an incompatible bundle before pulling its images.

#### Scenario: Host supports every required component
- **WHEN** every required component advertises support for the current Lerd host platform and architecture
- **THEN** Lerd allows the bundle installation to proceed

#### Scenario: A required image has no supported host platform
- **WHEN** any required component does not support the current Lerd host platform or architecture
- **THEN** Lerd refuses installation before fetching images and identifies the incompatible component and available platforms

### Requirement: Optional resource limits are enforceable
Bundle descriptors MAY set per-component CPU and memory limits only where the current Lerd runtime can enforce them. Unset limits SHALL use the runtime defaults, and resource limits SHALL NOT be presented as a minimum resource recommendation.

#### Scenario: A supported component limit is configured
- **WHEN** a bundle declares a valid CPU or memory limit on a host/runtime profile that supports enforcement
- **THEN** Lerd applies that limit to the component and reports the configured value

#### Scenario: A limit cannot be enforced on the current host
- **WHEN** a bundle declares a resource limit that the current host/runtime profile cannot enforce
- **THEN** Lerd rejects the bundle before pulling images and identifies the unsupported component and setting

### Requirement: Bundle updates and removal preserve recoverability
Lerd SHALL update and remove bundle components as a group while following the service data-retention policy and reporting incomplete operations.

#### Scenario: Update fails partway through
- **WHEN** one component cannot be updated
- **THEN** Lerd reports which components changed and which did not, and leaves persistent data available for retry or rollback

#### Scenario: Bundle is removed without a data wipe request
- **WHEN** a user removes a bundle without requesting data deletion
- **THEN** Lerd stops and removes its containers while retaining declared persistent data for recovery
