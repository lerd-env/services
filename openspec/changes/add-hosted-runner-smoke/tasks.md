# Tasks

## 1. Harden the hosted image smoke

- [x] 1.1 Keep the workflow opt-in with `workflow_dispatch`, read-only `contents` permission, `ubuntu-latest`, a finite timeout, and per-ref cancellation; verify these settings in `.github/workflows/runner-image-smoke.yml`.
- [x] 1.2 Read the image reference from `services/github-actions-runner.yaml`, reject a missing or malformed SHA-256 digest before pulling, then pull and inspect that same reference; verify both image steps use the preset-derived output.
- [x] 1.3 Invoke the already-pulled image with `--pull=never`, `--network=none`, and closed empty stdin; verify the check passes only on the expected missing-token diagnostic and fails on success or any other error.

## 2. Document the maintainer flow

- [x] 2.1 Document `gh-axi` dispatch, run listing, and run inspection in the runner section of `README.md`; verify the section says the smoke proves image availability and tokenless refusal only.

## 3. Validate the local and hosted checks

- [x] 3.1 Run `openspec validate add-hosted-runner-smoke --strict` and inspect `openspec status --change add-hosted-runner-smoke --json`; record any remaining hosted-only work as pending.
- [ ] 3.2 Validate `.github/workflows/runner-image-smoke.yml` syntax and inspect that its trigger, runner, permissions, timeout, concurrency, preset-sourced digest, and isolated container invocation match this contract.
- [ ] 3.3 Once the workflow and preset are available on the selected target repository ref, dispatch with `gh-axi workflow run` and inspect the completed result with `gh-axi run view`; confirm the evidence is limited to image availability and tokenless refusal.
