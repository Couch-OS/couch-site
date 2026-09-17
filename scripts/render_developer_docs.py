#!/usr/bin/env python3
"""Render Couch's canonical Markdown developer docs into the public site."""
import argparse
import html
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import markdown

if markdown.__version__ != "3.8.2":
    raise RuntimeError("developer documentation requires Markdown 3.8.2")

ROOT = Path(__file__).resolve().parents[1]
DOCS_PATH = Path("docs/development")
SHA = re.compile(r"[0-9a-f]{40}")
GITHUB_MAIN = "https://github.com/Couch-OS/couch/"
# Couch Markdown written before the repository moved still links here. GitHub
# redirects it, but those links must be pinned like current ones.
LEGACY_GITHUB_MAIN = "https://github.com/dangerouslaser/couch/"


@dataclass(frozen=True)
class Page:
    source: Path
    slug: str
    title: str
    description: str
    order: int
    body: str


def _origin_repository(couch: Path) -> str:
    remote = subprocess.check_output(
        ["git", "-C", str(couch), "remote", "get-url", "origin"], text=True
    ).strip()
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    return remote.removesuffix(".git").rstrip("/")


def _metadata(source: Path) -> tuple[dict[str, str], str]:
    lines = source.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    at = 0
    for at, line in enumerate(lines):
        if not line.strip():
            at += 1
            break
        if ":" not in line:
            raise ValueError(f"{source}: metadata must precede the first blank line")
        key, value = line.split(":", 1)
        values[key.strip().lower()] = value.strip()
    required = {"title", "description", "order"}
    if set(values) != required:
        raise ValueError(f"{source}: metadata keys must be exactly {sorted(required)}")
    return values, "\n".join(lines[at:]) + "\n"


def load_pages(couch: Path) -> list[Page]:
    docs = couch / DOCS_PATH
    if not docs.is_dir():
        raise ValueError(f"developer documentation is missing: {docs}")
    pages = []
    for source in sorted(docs.glob("*.md")):
        meta, body = _metadata(source)
        slug = source.stem
        try:
            order = int(meta["order"])
        except ValueError as error:
            raise ValueError(f"{source}: order must be an integer") from error
        pages.append(Page(source, slug, meta["title"], meta["description"], order, body))
    pages.sort(key=lambda page: (page.order, page.title.casefold()))
    if not pages or pages[0].slug != "index":
        raise ValueError("developer documentation needs an index.md with the lowest order")
    if len({page.order for page in pages}) != len(pages):
        raise ValueError("developer documentation page orders must be unique")
    return pages


def _pinned_links(rendered: str, repository: str, commit: str) -> str:
    pinned = repository + "/"
    for main in (GITHUB_MAIN, LEGACY_GITHUB_MAIN):
        rendered = rendered.replace(main + "blob/main/", pinned + f"blob/{commit}/")
        rendered = rendered.replace(main + "tree/main/", pinned + f"tree/{commit}/")
    rendered = re.sub(
        r'href="(?!https?://)([^"]+)\.md(#[^"]*)?"', r'href="\1.html\2"', rendered
    )
    return rendered


def _nav(pages: list[Page], current: str) -> str:
    links = []
    for page in pages:
        href = "index.html" if page.slug == "index" else f"{page.slug}.html"
        active = ' aria-current="page"' if page.slug == current else ""
        links.append(
            f'<a href="{href}"{active} data-doc-title="{html.escape(page.title)}" '
            f'data-doc-description="{html.escape(page.description)}">'
            f'<span>{html.escape(page.title)}</span><small>{html.escape(page.description)}</small></a>'
        )
    return "".join(links)


def _cards(pages: list[Page]) -> str:
    cards = []
    for page in pages:
        if page.slug == "index":
            continue
        search_value = re.sub(r"[^a-z0-9:+._-]+", " ", page.body.lower())
        search_value = " ".join(search_value.split())
        cards.append(
            f'<a class="developer-card" href="{page.slug}.html" '
            f'data-search-value="{html.escape(search_value)}">'
            f'<span class="developer-card-number">{page.order - 1:02d}</span>'
            f'<h2>{html.escape(page.title)}</h2><p>{html.escape(page.description)}</p>'
            '<span class="developer-card-link">Read the guide <span aria-hidden="true">→</span></span></a>'
        )
    return "".join(cards)


def _template(
    page: Page,
    pages: list[Page],
    content: str,
    repository: str,
    commit: str,
    preview: bool,
) -> str:
    title = html.escape(page.title)
    description = html.escape(page.description)
    canonical = "https://couch-os.dev/developers/" + (
        "" if page.slug == "index" else f"{page.slug}.html"
    )
    source_path = DOCS_PATH / page.source.name
    source = f"{repository}/blob/{commit}/{source_path.as_posix()}"
    edit = f"{repository}/edit/{commit}/{source_path.as_posix()}"
    preview_banner = (
        '<div class="preview-banner" role="note"><strong>Local preview.</strong> '
        "This page comes from an uncommitted development checkout.</div>"
        if preview
        else ""
    )
    search = (
        '<div class="developer-search"><label for="developer-search">Find a topic</label>'
        '<input id="developer-search" type="search" placeholder="Protocol, signing, testing…" '
        'autocomplete="off" data-developer-search><p data-search-status aria-live="polite"></p></div>'
        if page.slug == "index"
        else ""
    )
    cards = f'<section class="developer-cards" data-developer-cards>{_cards(pages)}</section>' if page.slug == "index" else ""
    component_styles = '<link rel="stylesheet" href="components.css">' if page.slug == "components" else ""
    component_script = '<script src="components.js" defer></script>' if page.slug == "components" else ""
    noindex = '<meta name="robots" content="noindex">' if preview else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{description}"><title>{title} — Couch developers</title>
<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="preload" href="../assets/InterVariable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="style.css">{component_styles}<link rel="canonical" href="{canonical}">{noindex}</head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="topbar wrap"><a class="brand" href="../" aria-label="Couch home">couch.</a><nav aria-label="Main navigation"><a href="../integrations.html">Integrations</a><a href="../usage/">Using Couch</a><a href="index.html" aria-current="page">Developers</a><a href="{repository}">GitHub <span aria-hidden="true">↗</span></a></nav></header>
{preview_banner}<main id="main" class="developer-shell wrap">
<aside class="developer-sidebar" aria-label="Developer documentation"><p class="eyebrow">DEVELOPER PREVIEW</p><a class="developer-home" href="index.html">Integration packages</a>{search}<nav aria-label="Developer topics">{_nav(pages, page.slug)}</nav></aside>
<article class="developer-copy">{content}{cards}<footer class="developer-source"><p>Documentation source at <code>{html.escape(commit[:12])}</code></p><div><a href="{source}">View Markdown</a><a href="{edit}">Suggest an edit</a></div></footer></article>
</main><footer class="wrap"><a class="brand" href="../">couch.</a><p>An independent project for the Sanytron Astrion HA100.<br>Developer preview; interfaces may change before release.</p><div class="licenses"><a href="../credits.html">Artwork &amp; licenses</a><a href="{repository}">Project source</a></div></footer>
<script src="docs.js" defer></script>{component_script}</body></html>'''


def render(couch: Path, destination: Path, repository: str, commit: str, preview: bool = False) -> list[Path]:
    couch = couch.resolve()
    destination = destination.resolve()
    if not SHA.fullmatch(commit):
        raise ValueError("developer documentation source commit must be a full 40-character SHA")
    parsed = urlparse(repository)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise ValueError("developer documentation repository must be an HTTPS GitHub URL")
    pages = load_pages(couch)
    output = destination / "developers"
    output.mkdir(parents=True, exist_ok=True)
    built = []
    for page in pages:
        content = markdown.markdown(
            page.body,
            extensions=["fenced_code", "sane_lists", "tables", "toc"],
            output_format="html5",
        )
        if page.slug == "components":
            marker = '<h2 id="component-library">'
            if content.count(marker) != 1:
                raise ValueError("components.md must contain one Component library heading")
            previews = (ROOT / "scripts/templates/component-previews.html").read_text(encoding="utf-8")
            content = content.replace(marker, previews + "\n" + marker, 1)
        content = _pinned_links(content, repository, commit)
        target = output / ("index.html" if page.slug == "index" else f"{page.slug}.html")
        target.write_text(
            _template(page, pages, content, repository, commit, preview),
            encoding="utf-8",
            newline="\n",
        )
        built.append(target)
    return built


def standalone_preview(couch: Path, destination: Path, commit: str) -> list[Path]:
    if destination.exists():
        raise ValueError("preview destination already exists; choose a new path")
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(
            ".git", ".github", "dist", "node_modules", "source-pin", ".DS_Store"
        ),
    )
    return render(couch, destination, _origin_repository(couch), commit, preview=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--couch-source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    couch_source = args.couch_source.resolve()
    source_commit = args.source_commit or subprocess.check_output(
        ["git", "-C", str(couch_source), "rev-parse", "HEAD"], text=True
    ).strip()
    if not args.preview:
        parser.error("standalone rendering is only for local previews; use --preview")
    pages = standalone_preview(couch_source, args.destination.resolve(), source_commit)
    print(f"Rendered {len(pages)} developer pages in {args.destination.resolve() / 'developers'}")
