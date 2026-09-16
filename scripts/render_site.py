#!/usr/bin/env python3
"""Render the deployable site from static source and a pinned Couch checkout."""
import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+-alpha\.[0-9]{8}\.[0-9]+$")


def pin():
    values = {}
    for line in (ROOT / "source-pin").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value
    if set(values) != {"repository", "commit"} or not re.fullmatch(r"[0-9a-f]{40}", values["commit"]):
        raise ValueError("source-pin must name one repository and a full 40-character commit")
    return values


def checked_source(path):
    values = pin()
    actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    remote = subprocess.check_output(["git", "-C", str(path), "remote", "get-url", "origin"], text=True).strip()
    if actual != values["commit"]:
        raise ValueError("Couch checkout is %s, source-pin requires %s" % (actual, values["commit"]))
    if remote.rstrip("/").removesuffix(".git") != values["repository"].rstrip("/").removesuffix(".git"):
        raise ValueError("Couch checkout origin does not match source-pin")
    dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty:
        raise ValueError("Couch checkout has tracked changes; use a clean checkout at source-pin")
    release = (path / "tools/release/current-release.txt").read_text(encoding="utf-8").strip()
    if not TAG.fullmatch(release):
        raise ValueError("Couch current-release.txt is not a promotion release tag: " + release)
    return release


def render(source, destination, couch):
    destination = destination.resolve()
    if destination == couch or couch.is_relative_to(destination) or destination.is_relative_to(couch):
        raise ValueError("destination must not be the Couch checkout, its ancestor, or its child")
    if destination == source or source.is_relative_to(destination):
        raise ValueError("destination must not replace the site source or its ancestor")
    tag = checked_source(couch)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        "wasm", ".DS_Store", ".git", ".github", "scripts", "tools", "guides",
        "dist", "node_modules", "source-pin", ".gitignore"))
    for path in destination.rglob("*"):
        if not path.is_file() or path.suffix not in (".html", ".xml", ".txt"):
            continue
        text = path.read_text(encoding="utf-8")
        text = text.replace("https://dangerouslaser.github.io/couch", "https://couch-os.dev")
        text = text.replace("{{COUCH_RELEASE_TAG}}", tag).replace("{{COUCH_RELEASE_VERSION}}", tag[1:])
        path.write_text(text, encoding="utf-8", newline="\n")
    leftover = [p for p in destination.rglob("*.html") if "{{COUCH_RELEASE_" in p.read_text(encoding="utf-8")]
    if leftover:
        raise ValueError("unrendered release token: " + str(leftover[0]))
    return tag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--couch-source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(render(ROOT, args.destination, args.couch_source.resolve()))
