"""Shared pytest fixtures for the ESWS smoke tests.

These tests run *inside* the app image on the docker-compose network (see
scripts/smoke.sh), so service hostnames (wps, dashboard, geoserver) resolve and
natcap.invest is importable. URLs are overridable via environment variables for
running against other deployments.

pytest loads this for every subdirectory, tests/unit included, so nothing here may
import at module level what only the stack tests need: requests is not installed
in the environment that runs the unit tests on its own.
"""
import os
import time

import pytest

WPS_URL = os.environ.get("WPS_URL", "http://wps:5000/wps")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://dashboard:8000")
GEOSERVER_URL = os.environ.get("GEOSERVER_URL", "http://geoserver:8080/geoserver")


def _wait(url, timeout=240, predicate=None):
    """Poll url until predicate(response) is true or timeout (seconds)."""
    import requests

    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if predicate is None or predicate(r):
                return r
            last = "status=%s" % r.status_code
        except requests.RequestException as exc:
            last = repr(exc)
        time.sleep(3)
    raise TimeoutError("Timed out waiting for %s (last: %s)" % (url, last))


@pytest.fixture(scope="session")
def wps_url():
    _wait(WPS_URL + "?service=WPS&request=GetCapabilities&version=1.0.0",
          predicate=lambda r: r.status_code == 200 and b"Capabilities" in r.content)
    return WPS_URL


@pytest.fixture(scope="session")
def dashboard_url():
    _wait(DASHBOARD_URL + "/", predicate=lambda r: r.status_code == 200)
    return DASHBOARD_URL


@pytest.fixture(scope="session")
def geoserver_url():
    _wait(GEOSERVER_URL + "/web/",
          predicate=lambda r: r.status_code in (200, 302, 401, 403))
    return GEOSERVER_URL
