#!/usr/bin/env python3
"""Checks on the renderer, run in CI beside the render itself.

Each case builds a throwaway store in a temp dir, renders it, and reads the
published trees back, so the checks describe what a binary would fetch rather
than how the renderer is written.
"""

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path(__file__).resolve()


def build_multi(root, schemas, legacy=None, trees=None):
    """A store with several schema trees. `schemas` maps version to its yaml."""
    (root / ".github" / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT.parent / "render_schema.py", root / ".github" / "scripts" / "render_schema.py")
    (root / "schema").mkdir()
    for version, body in schemas.items():
        (root / "schema" / f"{version}.yaml").write_text(body)
    (root / "services").mkdir()
    for name, body in (legacy or {}).items():
        (root / "services" / f"{name}.yaml").write_text(body)
    for version, files in (trees or {}).items():
        tree = root / "schema" / str(version) / "services"
        tree.mkdir(parents=True)
        for name, body in files.items():
            (tree / f"{name}.yaml").write_text(body)
    out = subprocess.run([sys.executable, str(root / ".github" / "scripts" / "render_schema.py")],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"render failed:\n{out.stdout}\n{out.stderr}")
    return out.stdout


def build(root, schema_yaml, legacy=None, top=None):
    (root / ".github" / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT.parent / "render_schema.py", root / ".github" / "scripts" / "render_schema.py")
    (root / "schema").mkdir()
    (root / "schema" / "2.yaml").write_text(schema_yaml)
    (root / "services").mkdir()
    for name, body in (legacy or {}).items():
        (root / "services" / f"{name}.yaml").write_text(body)
    top_dir = root / "schema" / "2" / "services"
    top_dir.mkdir(parents=True)
    for name, body in (top or {}).items():
        (top_dir / f"{name}.yaml").write_text(body)
    out = subprocess.run([sys.executable, str(root / ".github" / "scripts" / "render_schema.py")],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"render failed:\n{out.stdout}\n{out.stderr}")
    return out.stdout


def names_in(path):
    with open(path, "r", encoding="utf-8") as handle:
        return {e["name"] for e in json.load(handle).get("services", [])}


def case_introduces_is_withheld_from_older_schemas():
    """A definition a schema introduces reaches that schema's tree and no lower one."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        build(root,
              "schema: 2\nsince_lerd: \"1.36.0\"\nintroduces:\n  - newthing\nchanges: []\n",
              legacy={"oldthing": "name: oldthing\nimage: x\ndescription: d\ncategory: c\nicon: i\n"},
              top={"newthing": "name: newthing\nimage: y\ndescription: d\ncategory: c\nicon: i\n"})

        assert not (root / "services" / "newthing.yaml").exists(), \
            "an introduced definition must not be published to the older tree"
        assert (root / "schema" / "2" / "services" / "newthing.yaml").exists(), \
            "an introduced definition must stay in the tree that introduced it"
        assert "newthing" not in names_in(root / "services" / "index.json"), \
            "an introduced definition must not be listed in the older index"
        assert "newthing" in names_in(root / "schema" / "2" / "services" / "index.json"), \
            "an introduced definition must be listed in its own index"
        assert "oldthing" in names_in(root / "services" / "index.json"), \
            "an ordinary definition stays listed everywhere"
        assert "oldthing" in names_in(root / "schema" / "2" / "services" / "index.json"), \
            "an ordinary definition is listed in every schema's index"


def case_key_downgrade_still_applies():
    """A key a schema adds is still rendered away for the older tree."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        build(root,
              "schema: 2\nsince_lerd: \"1.36.0\"\nchanges:\n  - path: fancy\n    downgrade: drop\n",
              top={"thing": "name: thing\nimage: y\ndescription: d\ncategory: c\nicon: i\nfancy: true\n"})
        low = (root / "services" / "thing.yaml").read_text()
        high = (root / "schema" / "2" / "services" / "thing.yaml").read_text()
        assert "fancy" not in low, "the older tree must not carry a key the schema added"
        assert "fancy" in high, "the introducing tree keeps the key"


def case_guarded_drop_reads_the_source():
    """A `when` guard reads the document as authored, not as half rendered."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        build(root,
              "schema: 2\nsince_lerd: \"1.36.0\"\nchanges:\n"
              "  - path: flag\n    downgrade: drop\n"
              "  - path: dashboard\n    downgrade: drop\n    when: flag\n",
              top={"thing": "name: thing\nimage: y\ndescription: d\ncategory: c\nicon: i\n"
                            "flag: true\ndashboard: http://localhost:1/\n"})
        low = (root / "services" / "thing.yaml").read_text()
        assert "dashboard" not in low, \
            "a guarded drop must fire even when an earlier rule removed the key it reads"


def case_a_definition_authored_below_the_top_survives():
    """A definition authored at schema 2 is still found once schema 3 exists."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        build_multi(root,
                    {2: "schema: 2\nsince_lerd: \"1.36.0\"\nintroduces:\n  - gated\nchanges: []\n",
                     3: "schema: 3\nsince_lerd: \"1.40.0\"\nintroduces: []\nchanges:\n"
                        "  - path: newkey\n    downgrade: drop\n"},
                    trees={2: {"gated": "name: gated\nimage: g\ndescription: d\ncategory: c\nicon: i\n"},
                           3: {"fresh": "name: fresh\nimage: f\ndescription: d\ncategory: c\nicon: i\nnewkey: 1\n"}})

        assert (root / "schema" / "2" / "services" / "gated.yaml").exists(), \
            "a definition authored below the top tree must not be dropped"
        assert not (root / "services" / "gated.yaml").exists(), \
            "an introduced definition stays withheld from the tree below it"
        assert "gated" in names_in(root / "schema" / "2" / "services" / "index.json"), \
            "it stays listed in the schema that introduced it"
        assert "gated" in names_in(root / "schema" / "3" / "services" / "index.json"), \
            "a later schema still lists a definition introduced earlier"
        assert "gated" not in names_in(root / "services" / "index.json"), \
            "and the oldest tree still does not"


def main():
    cases = [v for k, v in sorted(globals().items()) if k.startswith("case_")]
    for case in cases:
        case()
        print(f"ok  {case.__name__}")
    print(f"\n{len(cases)} check(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
