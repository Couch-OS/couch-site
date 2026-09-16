#!/bin/sh
# Render this site with the actual pinned Couch UI preview, without copying it.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
couch_source=${COUCH_SOURCE:-}
destination=${SITE_DESTINATION:-$root/dist}
while [ "$#" -gt 0 ]; do
    case "$1" in
        --couch-source) couch_source=$2; shift 2 ;;
        --destination) destination=$2; shift 2 ;;
        *) echo "usage: $0 --couch-source PATH [--destination PATH]" >&2; exit 2 ;;
    esac
done
[ -n "$couch_source" ] || { echo "--couch-source is required" >&2; exit 2; }
python3 "$root/scripts/render_site.py" --couch-source "$couch_source" --destination "$destination"
"$couch_source/tools/build-preview.sh" --site-destination "$destination/wasm"
printf 'Couch site built in %s\n' "$destination"
