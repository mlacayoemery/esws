#!/usr/bin/env bash
#
# Install GeoServer for the bare-metal deployment (install.sh option 7).
#
# Version-matched to the container stack: docker-compose.yml runs
# docker.osgeo.org/geoserver:3.0.0, so bare metal installs 3.0.0 too.
#
# Uses the platform-independent binary, which bundles Jetty. The alternative --
# the WAR in a servlet container -- is worse here: GeoServer's WAR is still
# Java EE even at 3.0 (WEB-INF/web.xml declares xmlns=".../ns/javaee"), so it
# needs Tomcat 9, and Ubuntu dropped that package after 22.04 while shipping
# only the incompatible Tomcat 10. The bundled Jetty sidesteps all of that.
#
# GeoServer 3.0 requires Java 17 (see RUNNING.html in the distribution).
#
# Env overrides: GS_VERSION, GEOSERVER_HOME, GEOSERVER_DATA_DIR
set -euo pipefail

GS_VERSION="${GS_VERSION:-3.0.0}"
GEOSERVER_HOME="${GEOSERVER_HOME:-/opt/geoserver}"
GEOSERVER_DATA_DIR="${GEOSERVER_DATA_DIR:-/opt/geoserver_data}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

if ! command -v java >/dev/null 2>&1; then
    echo "java not found -- install openjdk-17-jre-headless first" >&2
    exit 1
fi

echo ">> Downloading GeoServer ${GS_VERSION} (platform-independent binary)"
curl -fsSL --retry 3 -o "$WORK/geoserver-bin.zip" \
    "https://sourceforge.net/projects/geoserver/files/GeoServer/${GS_VERSION}/geoserver-${GS_VERSION}-bin.zip/download"

echo ">> Installing into ${GEOSERVER_HOME}"
$SUDO rm -rf "${GEOSERVER_HOME}"
$SUDO mkdir -p "${GEOSERVER_HOME}"
$SUDO unzip -q "$WORK/geoserver-bin.zip" -d "${GEOSERVER_HOME}"
$SUDO chmod +x "${GEOSERVER_HOME}/bin/"*.sh

# Keep the catalog outside the install tree so upgrading GeoServer -- which
# replaces GEOSERVER_HOME wholesale -- cannot take the configured layers with it.
if [ ! -d "${GEOSERVER_DATA_DIR}" ] || [ -z "$($SUDO ls -A "${GEOSERVER_DATA_DIR}" 2>/dev/null)" ]; then
    echo ">> Seeding data directory ${GEOSERVER_DATA_DIR}"
    $SUDO mkdir -p "${GEOSERVER_DATA_DIR}"
    $SUDO cp -a "${GEOSERVER_HOME}/data_dir/." "${GEOSERVER_DATA_DIR}/"
else
    echo ">> Keeping existing data directory ${GEOSERVER_DATA_DIR}"
fi

echo ">> GeoServer ${GS_VERSION} installed. Start it with:"
echo "     GEOSERVER_DATA_DIR=${GEOSERVER_DATA_DIR} ${GEOSERVER_HOME}/bin/startup.sh"
echo "   or install the esws-geoserver systemd unit (install.sh option 8)."
echo "   Web UI: http://localhost:8080/geoserver/web"
