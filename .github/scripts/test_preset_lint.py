#!/usr/bin/env python3
"""Checks on the preset lint, run in CI beside it.

Each case builds a throwaway store with one fault and asserts the rule that
should catch it does, and that a clean preset passes every rule.
"""

import json
import pathlib
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import preset_lint  # noqa: E402

CLEAN = {
    "name": "queue",
    "label": "Queue",
    "description": "A queue",
    "image": "docker.io/acme/queue:2",
    "dashboard": "http://localhost:8090",
    "category": "messaging",
    "icon": "queue",
    "color": "#123abc",
    "data_dir": "/data",
    "env_vars": ["QUEUE_URL=http://lerd-queue:8090"],
}


def entry_of(doc):
    return {k: doc[k] for k in ("name", *preset_lint.INDEX_MIRRORED) if k in doc}


def lint(doc, entry=None, filename=None):
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        services = root / "services"
        services.mkdir()
        (services / f"{filename or doc['name']}.yaml").write_text(json.dumps(doc))
        index = [entry if entry is not None else entry_of(doc)]
        (services / "index.json").write_text(json.dumps({"services": index}))
        return [line for rule in preset_lint.RULES for line in rule(root)]


def expect(doc, needle, **kw):
    found = lint(doc, **kw)
    assert any(needle in f for f in found), (needle, found)


def main():
    assert lint(CLEAN) == [], lint(CLEAN)

    expect({**CLEAN, "label": " "}, "no `label`")
    expect(CLEAN, "has no `label`", entry={k: v for k, v in entry_of(CLEAN).items() if k != "label"})
    expect(CLEAN, "does not match the file name", filename="queues")
    expect({**CLEAN, "color": "var(--brand)"}, "not a plain hex literal")
    expect({**CLEAN, "env_vars": ["QUEUE_URL=https://queue.test"]}, "names a .test domain")
    expect({**CLEAN, "dashboard": "https://queue.test"}, "names a .test domain")
    expect({**CLEAN, "image": "docker.io/acme/queue:latest"}, "floats")
    expect({**CLEAN, "image": "docker.io/acme/queue"}, "floats")
    expect(CLEAN, "dashboard is", entry={**entry_of(CLEAN), "dashboard": "http://localhost:9999"})

    # A preset that keeps no data may float, as the README allows, and a digest
    # is as pinned as a tag.
    stateless = {k: v for k, v in CLEAN.items() if k != "data_dir"}
    assert lint({**stateless, "image": "docker.io/acme/queue:latest"}) == []
    assert lint({**CLEAN, "image": "docker.io/acme/queue@sha256:" + "a" * 64}) == []
    print("preset lint checks passed.")


if __name__ == "__main__":
    main()
