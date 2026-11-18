#!/usr/bin/env python3
"""Find preset images whose registry has a newer version than any the store pins.

Every image a preset pins is grouped by repository, and the registry's tags are
compared shape by shape: `pg18` only against `pgNN`, `3-management-alpine` only
against `N-management-alpine`, so variants and pre-releases never count. Pins
are compared to two parts at most, so a patch release alone stays quiet.
Prints the findings as JSON for the workflow to turn into issues; a registry
that cannot be read is listed in the job summary and fails the run.

Usage: check_upstream_images.py
"""

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
TAG = re.compile(r"^(\D*)(\d+(?:\.\d+)*)(.*)$")
# The OCI API answers on these hosts, not on the names images are written with.
REGISTRY_HOSTS = {"docker.io": "registry-1.docker.io"}


def parse_tag(tag):
    m = TAG.match(tag)
    if not m:
        return None
    nums = tuple(int(n) for n in m.group(2).split("."))
    return (m.group(1), len(nums), m.group(3)), nums


def newer_versions(pinned, upstream):
    """Return (version, newest tag) for each pinned shape the registry has outgrown."""
    newest_pin, majors = {}, set()
    for tag in pinned:
        parsed = parse_tag(tag)
        if parsed:
            shape, nums = parsed
            newest_pin[shape] = max(newest_pin.get(shape, nums), nums)
            # A bare major tag such as `13` already follows every 13.x release.
            if len(nums) == 1:
                majors.add((shape[0], shape[2], nums[0]))

    found = []
    # Shapes sort one-part first, so a new major pinned as `12` is reported
    # before the `13.0` the same release brings to the `12.3` pin.
    for shape, pin in sorted(newest_pin.items()):
        depth = min(len(pin), 2)
        candidates = [(nums, tag) for tag in upstream
                      if (p := parse_tag(tag)) and p[0] == shape for nums in [p[1]]]
        if not candidates:
            continue
        nums, tag = max(candidates)
        prefix, _, suffix = shape
        if nums[:depth] <= pin[:depth] or (prefix, suffix, nums[0]) in majors:
            continue
        if depth == 1:
            majors.add((prefix, suffix, nums[0]))
        found.append((prefix + ".".join(map(str, nums[:depth])) + suffix, tag))
    return found


def pinned_images(root):
    """Map each image repository to the services pinning it and their tags."""
    images = {}
    for path in sorted([*root.glob("services/*.yaml"), *root.glob("schema/*/services/*.yaml")]):
        preset = yaml.safe_load(path.read_text())
        refs = [preset.get("image")] + [v.get("image") for v in preset.get("versions") or []]
        for ref in filter(None, refs):
            repo, _, tag = ref.rpartition(":")
            entry = images.setdefault(repo, {"services": set(), "tags": set()})
            entry["services"].add(preset.get("label") or preset["name"])
            entry["tags"].add(tag)
    return images


def _get(url, token=None):
    req = urllib.request.Request(url, headers={"User-Agent": "lerd-services-upstream-check"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(req, timeout=30)


def _token(challenge):
    params = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
    realm = params.pop("realm")
    with _get(realm + "?" + urllib.parse.urlencode(params)) as resp:
        body = json.load(resp)
    return body.get("token") or body.get("access_token")


def list_tags(repo):
    host, _, name = repo.partition("/")
    base = f"https://{REGISTRY_HOSTS.get(host, host)}"
    url, token, tags = f"{base}/v2/{name}/tags/list?n=1000", None, []
    while url:
        try:
            resp = _get(url, token)
        except urllib.error.HTTPError as err:
            if err.code != 401 or token:
                raise
            token = _token(err.headers["WWW-Authenticate"])
            continue
        with resp:
            tags += json.load(resp).get("tags") or []
            link = re.search(r"<([^>]+)>;\s*rel=\"next\"", resp.headers.get("Link", ""))
        url = urllib.parse.urljoin(base, link.group(1)) if link else None
    return tags


def main():
    found, failed = [], []
    for repo, entry in sorted(pinned_images(ROOT).items()):
        if not any(parse_tag(t) for t in entry["tags"]):
            continue
        try:
            upstream = list_tags(repo)
        except (urllib.error.URLError, OSError) as err:
            failed.append(f"{repo} ({err})")
            continue
        for version, tag in newer_versions(entry["tags"], upstream):
            found.append({"repo": repo, "services": sorted(entry["services"]),
                          "pinned": sorted(entry["tags"]), "version": version, "tag": tag})

    print(json.dumps(found))
    if failed:
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as out:
                out.write("Could not read: " + ", ".join(failed) + "\n")
        print("Could not read: " + ", ".join(failed), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
