#!/usr/bin/env python3
"""Render the definitions that differ between schemas into their published trees.

Every binary in the field computes its own store URL and cannot be taught a new
one, so the unprefixed path has to keep carrying what those binaries expect.
That is the oldest schema still supported, and it is where a definition lives by
default: services/<name>.yaml is authored, published as it stands, and copied
nowhere.

A definition is authored in the highest schema tree it needs, and every tree
below renders down from it. One needing nothing newer is authored in services/
and published as it stands; one carrying a key that would be wrong to publish to
an older binary is authored in schema/N/services/ instead, and services/ gets the
downgrade rendered from it. A schema tree is sparse, holding only the definitions
authored there plus its own index, since the client tries its bases in order and
a 404 falls straight through to the tree below.

A schema may also introduce a definition outright, listing it under `introduces`.
That definition is not rendered into any tree below and does not appear in their
indexes, so a binary reading an older schema neither lists it nor can fetch it.
This is the version gate: a service that offers an older lerd nothing at all,
because what drives it shipped in a later release, is simply not published to it.

Usage: render_schema.py
"""

import copy
import json
import pathlib
import sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEGACY = ROOT / "services"
SCHEMA_DIR = ROOT / "schema"

INDEX_FIELDS = ["name", "description", "family", "dashboard", "image", "category",
                "icon", "color", "admin_for", "admin_rank", "depends_on",
                "versions", "default_version", "env_role"]


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def schemas():
    out = []
    for path in sorted(SCHEMA_DIR.glob("*.yaml"), key=lambda p: int(p.stem)):
        spec = load_yaml(path)
        out.append((int(spec["schema"]), spec))
    return out


def resolve(doc, path):
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
    """Render one change backwards, newer schema to older.

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
    out = copy.deepcopy(doc)
    for version, spec in sorted(specs, reverse=True):
        if version <= target:
            continue
        guard = copy.deepcopy(out)
        for change in spec.get("changes", []):
            apply_change(out, change, guard)
    return out


def dump(doc, path):
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(doc, handle, sort_keys=False, default_flow_style=False, allow_unicode=True)


def index_for(docs):
    entries = []
    for doc in sorted(docs, key=lambda d: d.get("name", "")):
        entries.append({f: doc[f] for f in INDEX_FIELDS
                        if f in doc and doc[f] not in (None, "", [], {})})
    return {"services": entries}


def write_index(path, published, docs, owned, drop=None):
    """Rewrite only the entries this render owns.

    The published index is hand-maintained and does not always match what a
    projection of the YAML would produce. Regenerating it wholesale would push
    those differences to every install as a change nobody asked for, so entries
    for definitions this render does not touch are carried through exactly as
    they stand.
    """
    entries = index_for(docs)["services"]
    fresh = {e["name"]: e for e in entries if e.get("name") in owned}
    drop = drop or set()
    out, seen = [], set()
    if published.exists():
        with open(published, "r", encoding="utf-8") as handle:
            for entry in json.load(handle).get("services", []):
                name = entry.get("name")
                seen.add(name)
                if name in drop:
                    continue
                out.append(fresh.get(name, entry))
    for entry in entries:
        if entry.get("name") not in seen:
            out.append(entry)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"services": out}, handle, indent=2)
        handle.write("\n")


def main():
    specs = schemas()
    if not specs:
        print("no schema deltas; nothing to render")
        return 0
    oldest = 1
    newest = max(v for v, _ in specs)

    # name -> the schema that introduced it. A tree below that schema neither
    # carries the definition nor lists it.
    introduced_at = {}
    for version, spec in specs:
        for name in spec.get("introduces", []) or []:
            introduced_at[name] = version

    def visible_at(name, version):
        return introduced_at.get(name, oldest) <= version

    # A definition is authored in the highest schema tree it needs, and every
    # tree below renders down from it. One that needs nothing newer is authored
    # in services/ and published as it stands.
    top = SCHEMA_DIR / str(newest) / "services"
    sources = {p.stem: load_yaml(p) for p in sorted(top.glob("*.yaml"))} if top.exists() else {}
    plain = {p.stem: load_yaml(p) for p in sorted(LEGACY.glob("*.yaml")) if p.stem not in sources}

    inert, withheld = [], []
    for name, doc in sorted(sources.items()):
        if not visible_at(name, oldest):
            withheld.append(name)
            (LEGACY / f"{name}.yaml").unlink(missing_ok=True)
            continue
        low = render_to(doc, oldest, specs)
        dump(low, LEGACY / f"{name}.yaml")
        if low == doc:
            inert.append(name)

    write_index(LEGACY / "index.json", LEGACY / "index.json",
                list(plain.values())
                + [render_to(d, oldest, specs) for n, d in sources.items() if visible_at(n, oldest)],
                set(sources), drop={n for n in sources if not visible_at(n, oldest)})
    print(f"schema {oldest}: {len(plain)} authored in place, "
          f"{len(sources) - len(withheld)} rendered -> services")

    for version, _ in sorted(specs):
        if version <= oldest:
            continue
        out_dir = SCHEMA_DIR / str(version) / "services"
        out_dir.mkdir(parents=True, exist_ok=True)
        carried = 0
        for name, doc in sorted(sources.items()):
            if not visible_at(name, version):
                (out_dir / f"{name}.yaml").unlink(missing_ok=True)
                continue
            # The newest tree is authored, not rendered: leave its bytes alone.
            if version < newest:
                high = render_to(doc, version, specs)
                if high != render_to(doc, oldest, specs):
                    dump(high, out_dir / f"{name}.yaml")
                    carried += 1
            else:
                carried += 1
        write_index(out_dir / "index.json", LEGACY / "index.json",
                    list(plain.values())
                    + [render_to(d, version, specs) for n, d in sources.items() if visible_at(n, version)],
                    set(sources), drop={n for n in sources if not visible_at(n, version)})
        print(f"schema {version}: {carried} definition(s) -> {out_dir.relative_to(ROOT)}")

    if withheld:
        print(f"withheld from older schemas: {', '.join(sorted(withheld))}")
    if inert:
        print(f"note: {', '.join(inert)} render the same in every schema and need no source")
    print(f"authored schema is {newest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
