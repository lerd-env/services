#!/usr/bin/env python3
"""Check that every preset carries what lerd needs to present it.

The schema guard answers whether an older lerd can still read the store. This
answers whether a definition is complete and consistent, so the two failures
never read the same: what this finds is something to fix in the definition,
not a change that breaks an install.

Usage: preset_lint.py [store-dir]
"""

import json
import pathlib
import re
import sys
import yaml

HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
TEST_DOMAIN = re.compile(r"\.test\b")
# The fields an index entry repeats from its preset, for the picker to render
# without fetching every definition.
INDEX_MIRRORED = ("label", "description", "dashboard", "image", "category", "icon", "color")


def presets(root):
    """Every preset file in a services/ tree, with its parsed document."""
    for path in sorted(pathlib.Path(root).rglob("*.yaml")):
        if path.parent.name != "services":
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                doc = yaml.safe_load(handle) or {}
        except yaml.YAMLError:
            continue
        yield path, doc


def indexes(root):
    """Every index.json in a services/ tree, keyed by its directory."""
    out = {}
    for path in sorted(pathlib.Path(root).rglob("index.json")):
        if path.parent.name != "services":
            continue
        with open(path, "r", encoding="utf-8") as handle:
            out[path.parent] = (path, json.load(handle).get("services", []))
    return out


def missing_labels(root):
    """lerd shows a service under its label, so every preset and entry names one."""
    missing = []
    for path, doc in presets(root):
        label = doc.get("label")
        if not isinstance(label, str) or not label.strip():
            missing.append(f"{path.relative_to(root)}: no `label`, the name lerd shows the service under")
    for path, entries in indexes(root).values():
        for entry in entries:
            if not str(entry.get("label", "")).strip():
                missing.append(f"{path.relative_to(root)}: entry `{entry.get('name')}` has no `label`")
    return missing


def misnamed(root):
    """lerd fetches <name>.yaml, so the file has to be named after the preset."""
    return [
        f"{path.relative_to(root)}: `name: {doc.get('name')}` does not match the file name"
        for path, doc in presets(root)
        if doc.get("name") != path.stem
    ]


def bad_colors(root):
    """A colour that is not a plain hex literal is dropped and the mark goes untinted."""
    return [
        f"{path.relative_to(root)}: `color: {doc['color']}` is not a plain hex literal like #003545"
        for path, doc in presets(root)
        if "color" in doc and not HEX_COLOR.fullmatch(str(doc["color"]))
    ]


def test_domains(root):
    """A .test domain written out breaks every install on another TLD, and every
    one that has not set the domain: a container or localhost URL is what lerd
    env points at the service's domain once it has one."""
    found = []
    for path, doc in presets(root):
        values = [str(v) for v in doc.get("env_vars") or []] + [str(doc.get("dashboard") or "")]
        for value in values:
            if TEST_DOMAIN.search(value):
                found.append(f"{path.relative_to(root)}: `{value}` names a .test domain; write the container or localhost URL instead")
    return found


def floating_data_images(root):
    """A preset that keeps data must not float on latest: a new image can change
    the data format under it. One with no data_dir may, as the README allows."""
    found = []
    for path, doc in presets(root):
        if not doc.get("data_dir"):
            continue
        images = [doc.get("image")] + [v.get("image") for v in doc.get("versions") or []]
        for image in filter(None, images):
            if "@" in image:
                continue
            last = image.rsplit("/", 1)[-1]
            if ":" not in last or last.endswith(":latest"):
                found.append(f"{path.relative_to(root)}: `{image}` floats, but the preset keeps data; pin a version tag")
    return found


def index_drift(root):
    """An index entry repeats its preset's presentation, and must say the same."""
    drift = []
    trees = indexes(root)
    for path, doc in presets(root):
        tree = trees.get(path.parent)
        if tree is None:
            continue
        index_path, entries = tree
        entry = next((e for e in entries if e.get("name") == doc.get("name")), None)
        if entry is None:
            drift.append(f"{path.relative_to(root)}: no entry in {index_path.relative_to(root)}")
            continue
        for key in INDEX_MIRRORED:
            if entry.get(key) != doc.get(key):
                drift.append(f"{index_path.relative_to(root)}: `{doc.get('name')}` {key} is {entry.get(key)!r}, the preset says {doc.get(key)!r}")
    return drift


RULES = (missing_labels, misnamed, bad_colors, test_domains, floating_data_images, index_drift)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    failures = [line for rule in RULES for line in rule(root)]
    for line in failures:
        print(f"error: {line}")
    if failures:
        print(f"\n{len(failures)} preset problem(s) to fix.")
        return 1
    print("preset lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
