"""Django dashboard smoke tests — key views return 200 on Django 4.2."""
import re

import pytest
import requests


def test_dashboard_home(dashboard_url):
    r = requests.get(dashboard_url + "/", timeout=30)
    assert r.status_code == 200, r.text[:500]


def test_dashboard_server_list(dashboard_url):
    r = requests.get(dashboard_url + "/server/WPS/", timeout=30)
    assert r.status_code == 200, r.text[:500]


def test_dashboard_job_list(dashboard_url):
    r = requests.get(dashboard_url + "/job/", timeout=30)
    assert r.status_code == 200, r.text[:500]


@pytest.fixture(scope="module")
def registered_wps_server(dashboard_url, wps_url):
    """A WPS server registered in the dashboard, returning its primary key.

    Everything below needs one: with no servers the list template never enters
    its row loop and the element views are unreachable, which is how both the
    missing ``server_wps_capabilities`` URL name and the owslib ``verbose``
    kwarg survived the Django 4.2 port unnoticed.

    Depends on wps_url so the WPS is actually answering first -- the dashboard
    calls GetCapabilities server-side to list processes, and the WPS takes some
    seconds to import all 26 InVEST models on start.
    """
    r = requests.get(
        "%s/server/WPS/register/Smoke WPS/url/%s" % (dashboard_url, wps_url),
        timeout=60)
    assert r.status_code == 200, r.text[:500]

    listing = requests.get(dashboard_url + "/server/WPS/", timeout=30)
    assert listing.status_code == 200, listing.text[:1000]
    pks = re.findall(r"/server/WPS/(\d+)/", listing.text)
    assert pks, listing.text[:1000]
    return max(int(p) for p in pks)


def test_dashboard_server_list_renders_a_registered_server(registered_wps_server,
                                                           dashboard_url, wps_url):
    """The row template must reverse every URL name it references."""
    r = requests.get(dashboard_url + "/server/WPS/", timeout=30)
    assert r.status_code == 200, r.text[:1000]
    assert wps_url in r.text


def test_dashboard_lists_wps_processes(registered_wps_server, dashboard_url):
    r = requests.get("%s/server/WPS/%d/element/" % (dashboard_url, registered_wps_server),
                     timeout=120)
    assert r.status_code == 200, r.text[:1000]
    assert "annual_water_yield" in r.text, r.text[:1000]


def test_dashboard_wps_process_detail(registered_wps_server, dashboard_url):
    """Describes a process through owslib -- the path that raised
    TypeError: WebProcessingService.__init__() got an unexpected keyword
    argument 'verbose' once owslib dropped that parameter."""
    r = requests.get(
        "%s/server/WPS/%d/element/annual_water_yield/" % (dashboard_url,
                                                          registered_wps_server),
        timeout=120)
    assert r.status_code == 200, r.text[:1000]
