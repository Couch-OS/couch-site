#!/usr/bin/env python3
"""Render the deployable site from static source and a pinned Couch checkout."""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from render_developer_docs import render as render_developer_docs

ROOT = Path(__file__).resolve().parents[1]
# Couch promotes releases under two tag shapes: dated alphas from the couch
# repository itself, and semver installer releases from couch-installer
# (its own tag scheme, installer-vX.Y.Z).
DATED_ALPHA_TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+-alpha\.[0-9]{8}\.[0-9]+$")
INSTALLER_TAG = re.compile(r"installer-v[0-9]+\.[0-9]+\.[0-9]+$")
INSTALLER_TAG_PREFIX = "installer-v"
# GitHub repository that publishes the installer launchers. Couch records it in
# tools/release/installer-repository.txt; commits older than that file published
# from dangerouslaser/couch.
RELEASE_REPOSITORY_SOURCE = "tools/release/installer-repository.txt"
RELEASE_REPOSITORIES = ("dangerouslaser/couch", "Couch-OS/couch", "Couch-OS/couch-installer")
LEGACY_RELEASE_REPOSITORY = "dangerouslaser/couch"
TOKEN = re.compile(r"\{\{COUCH_\w*(?:\}\})?")


def pin():
    values = {}
    for line in (ROOT / "source-pin").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value
    if set(values) != {"repository", "commit"} or not re.fullmatch(r"[0-9a-f]{40}", values["commit"]):
        raise ValueError("source-pin must name one repository and a full 40-character commit")
    return values


def release_repository(path):
    source = path / RELEASE_REPOSITORY_SOURCE
    if not source.exists():
        print("Couch checkout has no %s; using %s" % (RELEASE_REPOSITORY_SOURCE, LEGACY_RELEASE_REPOSITORY),
              file=sys.stderr)
        return LEGACY_RELEASE_REPOSITORY
    repository = source.read_text(encoding="utf-8").strip()
    if repository not in RELEASE_REPOSITORIES:
        raise ValueError("Couch %s names an unsupported release repository: %r" % (RELEASE_REPOSITORY_SOURCE, repository))
    return repository


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
    if not (DATED_ALPHA_TAG.fullmatch(release) or INSTALLER_TAG.fullmatch(release)):
        raise ValueError("Couch current-release.txt is not a promotion release tag: " + release)
    return release, release_repository(path)


def release_version(tag):
    """The user-visible version for a release tag, without its tag prefix."""
    if INSTALLER_TAG.fullmatch(tag):
        return tag[len(INSTALLER_TAG_PREFIX):]
    return tag[1:]


def render(source, destination, couch):
    destination = destination.resolve()
    if destination == couch or couch.is_relative_to(destination) or destination.is_relative_to(couch):
        raise ValueError("destination must not be the Couch checkout, its ancestor, or its child")
    if destination == source or source.is_relative_to(destination):
        raise ValueError("destination must not replace the site source or its ancestor")
    values = pin()
    tag, repository = checked_source(couch)
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
        text = text.replace("{{COUCH_RELEASE_TAG}}", tag).replace("{{COUCH_RELEASE_VERSION}}", release_version(tag))
        text = text.replace("{{COUCH_RELEASE_REPOSITORY}}", repository)
        leftover = TOKEN.search(text)
        if leftover:
            raise ValueError("unrendered release token %s in %s" % (leftover.group(0), path))
        path.write_text(text, encoding="utf-8", newline="\n")
    render_developer_docs(
        couch,
        destination,
        values["repository"].removesuffix(".git"),
        values["commit"],
    )
    return tag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--couch-source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(render(ROOT, args.destination, args.couch_source.resolve()))
