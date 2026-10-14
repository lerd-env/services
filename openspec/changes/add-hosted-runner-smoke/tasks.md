## Implementation

- [ ] Add a manual GitHub-hosted smoke workflow with least-privilege permissions, timeout, and concurrency cancellation.
- [ ] Read and validate the pinned image reference from the runner preset; pull and inspect the image.
- [ ] Verify the entrypoint fails when invoked without a registration token, without using credentials or secrets.
- [ ] Document dispatch and inspection using `gh-axi` in the repository README.

## Validation

- [ ] Validate the OpenSpec change with `openspec validate add-hosted-runner-smoke --strict` and inspect its status.
- [ ] Check workflow syntax and ensure it uses only `workflow_dispatch`, `ubuntu-latest`, and the preset-sourced digest.
- [ ] Once available on the target repository, dispatch with `gh-axi workflow run` and inspect the completed run with `gh-axi run view`.
