"""Render the README's service logos from the store's own marks.

The marks under services/ are monochrome by contract, which GitHub would draw
black and lose on a dark theme. This paints each one in its declared colour on
a white tile, so the README reads the same in either theme. A service with no
mark gets the lerd glyph its `icon` names, in its category's tint, which is how
the dashboard draws it too.

Run from the repo root after adding or changing a service:
    python3 .github/scripts/readme_logos.py
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
GLYPHS = ROOT / ".github" / "glyphs"
OUT = ROOT / ".github" / "logos"

# The -600 tones of lerd's per-category tints (presetCategories.ts).
CATEGORY_TINT = {
    "databases": "#4f46e5",
    "cache": "#d97706",
    "messaging": "#7c3aed",
    "search": "#0284c7",
    "mail": "#e11d48",
    "admin": "#059669",
    "storage": "#0891b2",
    "testing": "#c026d3",
    "other": "#6b7280",
}

TILE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\
<rect x="0.5" y="0.5" width="63" height="63" rx="14" fill="#ffffff" stroke="#e4e4e7"/>\
<svg x="{inset}" y="{inset}" width="{size}" height="{size}" viewBox="{viewbox}"{attrs}>{body}</svg></svg>
"""


def split(svg: str, source: str) -> tuple[str, str]:
    root = re.match(r'\s*<svg[^>]*viewBox="([^"]+)"[^>]*>(.*)</svg>\s*$', svg, re.S)
    if not root:
        sys.exit(f"{source} has no <svg viewBox=...> root")
    return root.group(1), root.group(2)


def services() -> list[dict]:
    # Newer schemas list presets older binaries cannot read, so the README
    # takes every index there is and lets a later one win a name.
    merged = {}
    for index in [ROOT / "services" / "index.json", *sorted(ROOT.glob("schema/*/services/index.json"))]:
        for entry in json.loads(index.read_text())["services"]:
            merged[entry["name"]] = entry
    return list(merged.values())


def render(entry: dict) -> str:
    name = entry["name"]
    mark = ROOT / "services" / f"{name}.svg"
    if mark.exists():
        viewbox, body = split(mark.read_text(), mark.name)
        return TILE.format(inset=13, size=38, viewbox=viewbox, attrs=f' fill="{entry["color"]}"', body=body)

    glyph = GLYPHS / f"{entry['icon']}.svg"
    if not glyph.exists():
        sys.exit(f"{name} has no mark and its icon {entry['icon']!r} has no .github/glyphs/{entry['icon']}.svg")
    color = entry.get("color") or CATEGORY_TINT[entry["category"]]
    viewbox, body = split(glyph.read_text(), glyph.name)
    attrs = f' fill="none" stroke="{color}"'
    return TILE.format(inset=12, size=40, viewbox=viewbox, attrs=attrs, body=body.replace("currentColor", color))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for entry in services():
        (OUT / f"{entry['name']}.svg").write_text(render(entry))
        print(f"wrote .github/logos/{entry['name']}.svg")


if __name__ == "__main__":
    main()
