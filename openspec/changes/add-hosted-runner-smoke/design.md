# Design: hosted runner image smoke check

## Workflow boundary

Add `.github/workflows/runner-image-smoke.yml` as an independent opt-in workflow. It has a single job on `ubuntu-latest`, `workflow_dispatch` only, read-only repository contents permission, a finite job timeout, and a concurrency group with `cancel-in-progress: true`. It does not edit or replace any required checks.

## Image source and validation

The job checks out the repository, extracts the top-level `image` field from `services/github-actions-runner.yaml`, and validates the resulting reference contains `@sha256:` followed by exactly 64 hexadecimal characters. It then pulls the exact reference and inspects the resulting image metadata. The workflow must not contain a copied image tag or digest.

## Safe startup check

Run the image's configured entrypoint with harmless placeholder URL/name inputs and closed, empty stdin. The command must return nonzero; a zero exit means startup proceeded without a token and fails the workflow. The check uses no GitHub token, runner token, repository secret, or persistent runner. An expected nonzero result confirms only the image's tokenless refusal path.

## Failure and scope

Missing or malformed preset data, pull/inspect errors, or tokenless startup success fail the job. Successful completion establishes that GitHub-hosted Ubuntu could pull and inspect the pinned image and that its entrypoint refused tokenless startup. It does not test registration, connectivity to GitHub, job execution, or the private Docker sidecar.

## Maintainer operation

Document dispatch with `gh-axi workflow run runner-image-smoke.yml --ref main --repo lerd-env/services`, then list and inspect the run with `gh-axi run list` and `gh-axi run view`. Dispatch is possible only after this workflow exists on the target repository's selected ref.
