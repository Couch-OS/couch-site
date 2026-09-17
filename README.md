# Couch site

This is the public landing page and usage guide for Couch. It publishes at
<https://couch-os.dev>. The production Slint interface stays in the public
[`dangerouslaser/couch`](https://github.com/dangerouslaser/couch) repository;
this repository compiles that pinned checkout to WebAssembly during a site
build. No device UI is copied here.

`source-pin` records the Couch repository and exact full commit used for a
site build. Update it only with a reviewed Couch commit. `index.html` uses
release placeholders that `scripts/render_site.py` fills from the pinned
checkout: the tag from `tools/release/current-release.txt`, and the GitHub
repository that publishes the installer from
`tools/release/installer-repository.txt` (`dangerouslaser/couch` when the pinned
commit predates that file). Do not put a release tag or release repository in
the site source. The developer knowledge base follows the same rule: its canonical
Markdown lives in the pinned checkout under `docs/development/`, and the build
renders that exact revision into `developers/`. A Couch documentation change is
published only after this repository deliberately advances `source-pin`.

## Local build and checks

Install Rust's `wasm32-unknown-unknown` target and wasm-bindgen 0.2.127 as
documented by Couch, then obtain a checkout at the exact source-pin commit.
Install the pinned documentation dependency in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install --requirement requirements-docs.txt
```

```sh
PYTHON=$PWD/.venv/bin/python scripts/build-site.sh \
  --couch-source ../couch --destination dist
python3 -m http.server 8098 --directory dist
# In another terminal, with Playwright 1.57.0 installed:
SITE_URL=http://127.0.0.1:8098/ SITE_DIRECTORY=$PWD/dist \
  COUCH_SOURCE=../couch NODE_PATH=/path/to/node_modules \
  node tools/tests/site-demo.cjs
SITE_URL=http://127.0.0.1:8098/ SITE_DIRECTORY=$PWD/dist \
  COUCH_SOURCE=../couch NODE_PATH=/path/to/node_modules \
  node tools/tests/ha-preview.cjs
SITE_URL=http://127.0.0.1:8098/ SITE_DIRECTORY=$PWD/dist \
  COUCH_SOURCE=../couch NODE_PATH=/path/to/node_modules \
  node tools/tests/site-usage.cjs
SITE_URL=http://127.0.0.1:8098/ SITE_DIRECTORY=$PWD/dist \
  COUCH_SOURCE=../couch NODE_PATH=/path/to/node_modules \
  node tools/tests/site-developers.cjs
```

`dist/` and its WASM bundle and screenshots are generated. The browser checks
exercise the actual production Slint component tree with local fixtures only;
they do not contact a remote or an integration.

To preview uncommitted developer Markdown without changing `source-pin` or
building the Slint demo, render a disposable site shell:

```sh
.venv/bin/python scripts/render_developer_docs.py \
  --couch-source ../couch --destination /tmp/couch-developer-preview --preview
python3 -m http.server 8098 --directory /tmp/couch-developer-preview
```

Preview output is marked local and excluded from indexing. A production build
still requires a clean Couch checkout at the exact pinned commit.

The site files and their adapted source are licensed under GPL-3.0-or-later;
see `COPYING`. Font and icon notices remain adjacent to their assets.
