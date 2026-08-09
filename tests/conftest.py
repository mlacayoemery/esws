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
    # The login page rather than "/": every dashboard view requires a login now,
    # so "/" redirects here anyway, and waiting on it would only prove the
    # redirect works.
    _wait(DASHBOARD_URL + "/accounts/login/",
          predicate=lambda r: r.status_code == 200)
    return DASHBOARD_URL


@pytest.fixture(scope="session")
def dashboard(dashboard_url):
    """A requests.Session signed in as the dashboard administrator.

    The dashboard is multi-user: an anonymous request is redirected to the login
    page, and a signed-in non-admin sees only their own rows. These tests assert
    on what the stack as a whole produces, so they run as the admin -- the view
    that matches how the dashboard behaved before there were accounts.

    Django's login form is CSRF-protected, so the token has to be read from the
    login page and sent back with the credentials and the cookie.
    """
    import requests

    user = os.environ.get("DASHBOARD_ADMIN_USER", "admin")
    password = os.environ.get("DASHBOARD_ADMIN_PASS", "esws-admin")

    session = requests.Session()
    login_url = dashboard_url + "/accounts/login/"
    page = session.get(login_url, timeout=30)
    token = session.cookies.get("csrftoken")
    assert token, "no csrftoken cookie from %s: %s" % (login_url, page.text[:300])

    posted = session.post(login_url,
                          data={"username": user, "password": password,
                                "csrfmiddlewaretoken": token, "next": "/"},
                          headers={"Referer": login_url},
                          timeout=30, allow_redirects=True)
    assert posted.status_code == 200, posted.text[:500]
    assert "sessionid" in session.cookies, (
        "signing in as %s did not set a session cookie -- is DJANGO_SUPERUSER_* "
        "set on the dashboard service? %s" % (user, posted.text[:500]))
    return session


@pytest.fixture(scope="session")
def geoserver_url():
    _wait(GEOSERVER_URL + "/web/",
          predicate=lambda r: r.status_code in (200, 302, 401, 403))
    return GEOSERVER_URL
