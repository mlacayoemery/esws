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
set -euo pipefail
cd "$(dirname "$0")/.."

echo ">> Building images"
docker compose build

echo ">> Starting stack"
docker compose up -d

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
  wps sh -c "pip install --quiet -r requirements/dev.txt && python -m pytest tests/ -v"
