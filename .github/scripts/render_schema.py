#!/usr/bin/env python3
"""Render the authored definitions into one published tree per schema.

Definitions are authored under sources/ in the newest schema. Every binary in
the field computes its own store URL and cannot be taught a new one, so the
legacy unprefixed path has to carry the oldest schema still supported, and each
later schema gets a prefixed tree that only a binary knowing about it asks for.

A schema file states the delta from the one before it and how to render back
down: `drop` removes a key, `join` collapses a list into a delimited string,
`rename` moves one. A change may carry `when: <path>`, applying only to a
document where that path is truthy, which is how a key valid in both schemas can
still be wrong to publish to the older one.

Usage: render_schema.py [--check]
"""

import copy
import json
import pathlib
import shutil
import sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCES = ROOT / "sources"
SCHEMA_DIR = ROOT / "schema"

# Fields an index entry carries, in the order the published index uses them.
INDEX_FIELDS = ["name", "description", "family", "dashboard", "image", "category",
                "icon", "color", "admin_for", "admin_rank", "depends_on",
                "versions", "default_version", "env_role"]


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def schemas():
    """Every schema file, oldest first. Schema 1 is implicit and has no file."""
    out = []
    for path in sorted(SCHEMA_DIR.glob("*.yaml"), key=lambda p: int(p.stem)):
        spec = load_yaml(path)
        out.append((int(spec["schema"]), spec))
    return out


def resolve(doc, path):
    """Read a dotted path out of a document, or None."""
    node = doc
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def drop(doc, path):
    parts = path.split(".")
    node = doc
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            return
        node = node[part]
    if isinstance(node, dict):
        node.pop(parts[-1], None)


def apply_change(doc, change, guard):
    """Render one change backwards, from the newer schema to the older one.

    A `when` guard reads the document as it entered this schema's step, not the
    half-rendered one: a rule commonly depends on a key an earlier rule in the
    same step has already dropped.
    """
    if "when" in change and not resolve(guard, change["when"]):
        return
    path, how = change["path"], change["downgrade"]
    if how == "drop":
        drop(doc, path)
    elif isinstance(how, dict) and "join" in how:
        value = resolve(doc, path)
        if isinstance(value, list):
            parts = path.split(".")
            node = doc
            for part in parts[:-1]:
                node = node[part]
            node[parts[-1]] = how["join"].join(str(v) for v in value)
    elif isinstance(how, dict) and "rename" in how:
        value = resolve(doc, path)
        if value is not None:
            drop(doc, path)
            doc[how["rename"]] = value
    else:
        raise SystemExit(f"unknown downgrade {how!r} for {path}")


def render_to(doc, target, specs):
    """Render a newest-schema document down to the target schema."""
    out = copy.deepcopy(doc)
    for version, spec in sorted(specs, reverse=True):
        if version <= target:
            continue
        guard = copy.deepcopy(out)
        for change in spec.get("changes", []):
            apply_change(out, change, guard)
    return out


def index_for(docs):
    entries = []
    for doc in sorted(docs, key=lambda d: d.get("name", "")):
        entry = {f: doc[f] for f in INDEX_FIELDS if f in doc and doc[f] not in (None, "", [], {})}
        entries.append(entry)
    return {"services": entries}


def write_tree(out_dir, docs, assets):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for name, doc in sorted(docs.items()):
        with open(out_dir / f"{name}.yaml", "w", encoding="utf-8") as handle:
            yaml.safe_dump(doc, handle, sort_keys=False, default_flow_style=False, allow_unicode=True)
    for asset in assets:
        shutil.copy2(asset, out_dir / asset.name)
    with open(out_dir / "index.json", "w", encoding="utf-8") as handle:
        json.dump(index_for(list(docs.values())), handle, indent=2)
        handle.write("\n")


def main():
    specs = schemas()
    newest = max(v for v, _ in specs) if specs else 1
    src = SOURCES / "services"
    sources = {p.stem: load_yaml(p) for p in sorted(src.glob("*.yaml")) if p.name != "index.json"}
    assets = sorted(src.glob("*.svg"))

    targets = {1: ROOT / "services"}
    for version, _ in specs:
        if version > 1:
            targets[version] = ROOT / "schema" / str(version) / "services"

    for version, out_dir in sorted(targets.items()):
        rendered = {n: render_to(d, version, specs) for n, d in sources.items()}
        write_tree(out_dir, rendered, assets)
        print(f"schema {version}: {len(rendered)} definition(s) -> {out_dir.relative_to(ROOT)}")
    print(f"authored schema is {newest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
