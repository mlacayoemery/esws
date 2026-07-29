#!/usr/bin/env bash
#
# Download and unpack the InVEST sample datasets used by the demo and the
# model tests.
#
# Cached under $INVEST_DATA_ROOT (default /store/invest): archives/ holds the
# downloaded zips, samples/ the unpacked trees. Both are skipped if already
# present, so re-running is cheap and offline-safe once primed. Nothing here
# lands in the repo -- the full set is ~380MB.
#
# Env: INVEST_DATA_ROOT, INVEST_VERSION
set -euo pipefail

INVEST_VERSION="${INVEST_VERSION:-3.20.0}"
ROOT="${INVEST_DATA_ROOT:-/store/invest}"
ARCHIVES="$ROOT/archives"
SAMPLES="$ROOT/samples"
BASE="https://storage.googleapis.com/releases.naturalcapitalproject.org/invest/${INVEST_VERSION}/data"

mkdir -p "$ARCHIVES" "$SAMPLES"

echo ">> Listing sample archives for InVEST ${INVEST_VERSION}"
LIST="$ARCHIVES/.index.json"
if [ ! -s "$LIST" ]; then
    curl -fsSL --retry 3 -o "$LIST" \
        "https://storage.googleapis.com/storage/v1/b/releases.naturalcapitalproject.org/o?prefix=invest/${INVEST_VERSION}/data/&fields=items(name,size)&maxResults=500"
fi

NAMES=$(python3 -c "
import json
d = json.load(open('$LIST'))
for i in d.get('items', []):
    n = i['name'].split('/')[-1]
    if n.endswith('.zip'):
        print(n)
")

for name in $NAMES; do
    target="$ARCHIVES/$name"
    if [ -s "$target" ]; then
        echo "   cached   $name"
    else
        echo "   fetching $name"
        curl -fsSL --retry 3 -o "$target.part" "$BASE/$name"
        mv "$target.part" "$target"
    fi

    dest="$SAMPLES/${name%.zip}"
    if [ -d "$dest" ]; then
        continue
    fi
    mkdir -p "$dest"
    unzip -q -o "$target" -d "$dest" || {
        echo "   WARNING: could not unpack $name" >&2
        rmdir "$dest" 2>/dev/null || true
    }
done

echo ">> Sample data ready under $SAMPLES"
du -sh "$ROOT" 2>/dev/null | awk '{print "   total cached: " $1}'
