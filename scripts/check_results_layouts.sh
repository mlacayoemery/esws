#!/usr/bin/env bash
#
# Exercise every ESWS_RESULTS_LAYOUT / ESWS_VECTOR_BACKEND combination.
#
#   make check-layouts
#
# Not part of `make smoke`: each combination restarts the wps service so the
# server picks up the new environment, and then runs a model, so this takes
# minutes rather than seconds.
#
# For each combination it runs annual_water_yield with uploads on and asserts
# what actually landed on GeoServer -- a workspace per run, or one series layer
# gaining a granule.
set -uo pipefail
cd "$(dirname "$0")/.."

# Host ports live in .env, which docker compose reads and this shell does not.
if [ -f .env ]; then
    set -a; . ./.env; set +a
fi

GS="http://localhost:${GEOSERVER_HOST_PORT:-8080}/geoserver"
AUTH="${GEOSERVER_USER:-admin}:${GEOSERVER_PASS:-geoserver}"
FAILURES=0

workspaces() { curl -s -u "$AUTH" "$GS/rest/workspaces.json" \
    | python3 -c "import sys,json;print(' '.join(w['name'] for w in json.load(sys.stdin).get('workspaces',{}).get('workspace',[])))"; }

granules() {  # workspace layer -> number of granules in the mosaic index
    curl -s -u "$AUTH" \
      "$GS/rest/workspaces/$1/coveragestores/$2/coverages/$2/index/granules.json" \
      | python3 -c "import sys,json
try: print(len(json.load(sys.stdin).get('features',[])))
except Exception: print(0)"
}

run_once() {  # layout backend
    local layout="$1" backend="$2"
    echo ">> layout=$layout vectors=$backend"
    ESWS_RESULTS_LAYOUT="$layout" ESWS_VECTOR_BACKEND="$backend" \
        docker compose up -d --force-recreate wps >/dev/null 2>&1
    # The server imports 26 models before it answers.
    for _ in $(seq 1 40); do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
            "http://localhost:${WPS_HOST_PORT:-5000}/wps?service=WPS&version=1.0.0&request=GetCapabilities" || true)
        [ "$code" = "200" ] && break
        sleep 5
    done
    docker compose run --rm --no-deps -T \
        -e ESWS_RESULTS_LAYOUT="$layout" -e ESWS_VECTOR_BACKEND="$backend" \
        wps python scripts/publish_one.py >/dev/null 2>&1 || true
}

check() {  # description, condition already evaluated by the caller
    if [ "$1" = "1" ]; then echo "   ok   $2"; else echo "   FAIL $2"; FAILURES=$((FAILURES+1)); fi
}

echo ">> Loading the demo (idempotent)"
docker compose run --rm --no-deps -T wps python scripts/load_demo.py >/dev/null 2>&1 || true

echo ">> GeoServer at $GS"

# --- run layout ------------------------------------------------------------
for backend in files postgis; do
    before=$(workspaces | tr ' ' '\n' | grep -c '^run_' || true)
    run_once run "$backend"
    after=$(workspaces | tr ' ' '\n' | grep -c '^run_' || true)
    [ "$after" -gt "$before" ] && ok=1 || ok=0
    check "$ok" "layout=run vectors=$backend -> a new run_* workspace ($before -> $after)"
done

# --- series layout ---------------------------------------------------------
SERIES_WS="${ESWS_SERIES_WORKSPACE:-series}"
LAYER="annual_water_yield_wyield"
before=$(granules "$SERIES_WS" "$LAYER")
run_once series postgis
after=$(granules "$SERIES_WS" "$LAYER")
[ "$after" -gt "$before" ] && ok=1 || ok=0
check "$ok" "layout=series -> the raster series gained a granule ($before -> $after)"

dims=$(curl -s "$GS/$SERIES_WS/ows?service=WMS&version=1.3.0&request=GetCapabilities" \
       | grep -c '<Dimension name="time"' || true)
[ "$dims" -gt 0 ] && ok=1 || ok=0
check "$ok" "layout=series -> the series advertises a time dimension"

# A vector series without PostGIS must refuse rather than publish something
# that cannot be appended to.
run_once series files
refused=$(docker compose logs --tail 200 wps 2>&1 | grep -c "ESWS_VECTOR_BACKEND=postgis" || true)
[ "$refused" -gt 0 ] && ok=1 || ok=0
check "$ok" "layout=series vectors=files -> vectors refused, with the reason"

echo ">> Restoring the default combination"
docker compose up -d --force-recreate wps >/dev/null 2>&1

if [ "$FAILURES" -eq 0 ]; then
    echo ">> ALL LAYOUT COMBINATIONS OK"
else
    echo ">> $FAILURES check(s) failed"; exit 1
fi
