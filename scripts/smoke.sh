#!/usr/bin/env bash
#
# Containerized smoke test for the ESWS stack — the successor to demo_localhost.sh.
#
# Brings up wps + dashboard + fileserver + geoserver, then runs the pytest suite
# from inside the app image *on the compose network* (so it resolves the wps /
# dashboard / geoserver hostnames and can import natcap.invest).
#
# Env:
#   KEEP_UP=1   leave the stack running after the tests (default: tear down)
#   DEMO=1      load the demo data first, so the tests that need registered
#               sample data run instead of skipping (adds a few minutes, and
#               downloads ~2GB of InVEST samples on a cold cache)
set -euo pipefail
cd "$(dirname "$0")/.."

echo ">> Building images"
docker compose build

echo ">> Starting stack"
docker compose up -d

if [ "${DEMO:-0}" = "1" ]; then
  echo ">> Loading demo data"
  ./scripts/fetch_invest_samples.sh
  docker compose run --rm --no-deps wps python scripts/load_demo.py
fi

cleanup() {
  if [ "${KEEP_UP:-0}" != "1" ]; then
    echo ">> Tearing down stack"
    docker compose down -v
  fi
}
trap cleanup EXIT

echo ">> Running smoke tests (inside app image, on compose network)"
docker compose run --rm --no-deps \
  -e WPS_URL=http://wps:5000/wps \
  -e DASHBOARD_URL=http://dashboard:8000 \
  -e GEOSERVER_URL=http://geoserver:8080/geoserver \
  -e FILESERVER_URL=http://fileserver:8001 \
  wps sh -c "pip install --quiet -r requirements/dev.txt && python -m pytest tests/ -v"
