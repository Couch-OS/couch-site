# Couch site

This is the public landing page and usage guide for Couch. It publishes at
<https://couch-os.dev>. The production Slint interface stays in the public
[`dangerouslaser/couch`](https://github.com/dangerouslaser/couch) repository;
this repository compiles that pinned checkout to WebAssembly during a site
build. No device UI is copied here.

`source-pin` records the Couch repository and exact full commit used for a
site build. Update it only with a reviewed Couch commit. `index.html` uses
release placeholders that `scripts/render_site.py` fills from the pinned
checkout's `tools/release/current-release.txt`; do not put a release tag in the
site source.

## Local build and checks

Install Rust's `wasm32-unknown-unknown` target and wasm-bindgen 0.2.127 as
documented by Couch, then obtain a checkout at the exact source-pin commit.

```sh
scripts/build-site.sh --couch-source ../couch --destination dist
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
```

`dist/` and its WASM bundle and screenshots are generated. The browser checks
exercise the actual production Slint component tree with local fixtures only;
they do not contact a remote or an integration.

The site files and their adapted source are licensed under GPL-3.0-or-later;
see `COPYING`. Font and icon notices remain adjacent to their assets.
