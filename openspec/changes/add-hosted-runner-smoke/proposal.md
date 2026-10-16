# Add an opt-in hosted runner image smoke check

## Why

The `github-actions-runner` preset distributes a runner image pinned by manifest digest. Maintainers need a low-risk way to check that the published image remains pullable and that its startup path refuses registration when no token is supplied. GitHub-hosted jobs are temporary and do not require creating or registering a persistent runner.

## What changes

Add a manually dispatched workflow on `ubuntu-latest`. It reads `services/github-actions-runner.yaml`, requires the image to include an immutable SHA-256 digest, pulls and inspects that exact image, and invokes its entrypoint without a token to verify that it refuses registration. Document dispatch and run inspection through `gh-axi`.

This is repository CI tooling only. It does not change service behavior or the required schema guard, branch protection, secrets, or runner registration.

## User stories and acceptance criteria

### Maintainer checks the published runner image safely

- **Given** the runner preset contains a digest-pinned image reference, **when** a maintainer dispatches the smoke workflow, **then** the job runs on `ubuntu-latest`, reads the reference from the preset, pulls and inspects that image, and verifies tokenless startup fails.
- **Given** the preset image is mutable or lacks a SHA-256 digest, **when** the workflow runs, **then** it fails before pulling an unpinned image.
- **Given** multiple dispatches overlap, **when** a newer run starts, **then** GitHub cancels the older run in the same concurrency group.
- **Given** the smoke workflow completes, **when** a maintainer inspects it with `gh-axi`, **then** the run demonstrates image availability and tokenless rejection only; it makes no claim of runner registration or full job execution.

## Non-functional requirements

- Trigger only with `workflow_dispatch`.
- Grant only `contents: read`; use no secrets or registration token.
- Use a GitHub-hosted `ubuntu-latest` runner, never a self-hosted label.
- Set a job timeout and concurrency cancellation.

## Deferred ideas

- Registering a persistent repository runner or running jobs on it; that needs separate, trusted private-repository operations.
- Testing full runner operation, sidecar Docker behavior, or executing a workflow job through the runner.
- Automatically triggering this smoke check on pushes or releases.

## Assumptions

- The `github-actions-runner` preset and its published image digest are present in `lerd-env/services` before this workflow is merged there.
- The image entrypoint exits nonzero when required registration inputs, including its token on stdin, are absent.
