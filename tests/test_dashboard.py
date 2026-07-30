"""Django dashboard smoke tests — key views return 200 on Django 4.2."""
import re
import time

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


def test_generated_form_renders_for_every_process(registered_wps_server,
                                                  dashboard_url, wps_url):
    """Every advertised process must produce a job form.

    The form is generated from DescribeProcess, so a process whose inputs the
    generator cannot map would 500 here rather than at the moment a user picks
    it out of the list.
    """
    caps = requests.get(wps_url, params={"service": "WPS", "version": "1.0.0",
                                         "request": "GetCapabilities"}, timeout=60)
    ids = sorted(set(re.findall(r"<ows:Identifier>([^<]+)</ows:Identifier>", caps.text)))
    assert len(ids) >= 20, ids

    broken = []
    for process_id in ids:
        r = requests.get("%s/server/%d/execute/%s/" % (dashboard_url,
                                                       registered_wps_server,
                                                       process_id), timeout=120)
        if r.status_code != 200:
            broken.append("%s -> %s" % (process_id, r.status_code))
    assert not broken, broken


def test_generated_form_offers_registered_data(registered_wps_server, dashboard_url):
    """Spatial inputs become dropdowns of registered sources, not free text.

    This is what the hand-built water yield form did for one model; the
    generated form derives it for all of them from the InVEST type the WPS
    publishes on each input.
    """
    r = requests.get("%s/server/%d/execute/annual_water_yield/"
                     % (dashboard_url, registered_wps_server), timeout=120)
    assert r.status_code == 200, r.text[:1000]
    # lulc_path is a raster input, so it must render as a select
    assert re.search(r'<select[^>]*name="lulc_path"', r.text), r.text[:2000]


@pytest.fixture(scope="module")
def registered_template(dashboard_url, wps_url):
    """A Templates source pointing at the same WPS, returning its primary key."""
    r = requests.get("%s/server/TPL/register/Smoke Template/url/%s"
                     % (dashboard_url, wps_url), timeout=60)
    assert r.status_code == 200, r.text[:500]

    listing = requests.get(dashboard_url + "/server/TPL/", timeout=30)
    assert listing.status_code == 200, listing.text[:1000]
    pks = re.findall(r"/server/TPL/(\d+)/", listing.text)
    assert pks, listing.text[:1000]
    return max(int(p) for p in pks)


def test_dashboard_has_a_templates_section(registered_template, dashboard_url):
    r = requests.get(dashboard_url + "/", timeout=30)
    assert r.status_code == 200, r.text[:500]
    assert "Templates" in r.text
    # Templates are also ServerWPS rows; they must not show up twice.
    wps_list = requests.get(dashboard_url + "/server/WPS/", timeout=30)
    assert "Smoke Template" not in wps_list.text, wps_list.text[:1000]


def test_template_lists_the_same_processes(registered_template, dashboard_url):
    r = requests.get("%s/server/TPL/%d/element/" % (dashboard_url, registered_template),
                     timeout=120)
    assert r.status_code == 200, r.text[:1000]
    assert "annual_water_yield" in r.text


def test_template_process_detail_and_its_new_job_link(registered_template,
                                                      dashboard_url):
    """Walk the click-through: template -> process -> new job.

    Every per-type dispatch table in views has to know about TPL. The process
    detail page was missed and raised KeyError, so this covers the whole path
    rather than just the list and the form.
    """
    detail = requests.get("%s/server/TPL/%d/element/annual_water_yield/"
                          % (dashboard_url, registered_template), timeout=120)
    assert detail.status_code == 200, detail.text[:1000]

    # The "new job" link must carry the template's pk, or the form it opens
    # would be the unprefilled one.
    assert 'href="/server/%d/execute/annual_water_yield/"' % registered_template \
        in detail.text, detail.text[:2000]


def test_template_form_is_prefilled_from_the_sample_datastack(registered_template,
                                                              registered_wps_server,
                                                              dashboard_url):
    """A template's job form arrives carrying InVEST's own sample arguments.

    Checked on a scalar rather than a dropdown so it holds without the demo
    data being published: annual_water_yield's datastack sets results_suffix to
    "gura" and seasonality_constant to 5. The plain WPS source must stay empty.
    """
    tpl = requests.get("%s/server/%d/execute/annual_water_yield/"
                       % (dashboard_url, registered_template), timeout=120)
    assert tpl.status_code == 200, tpl.text[:1000]
    assert 'value="gura"' in tpl.text, tpl.text[:2000]

    plain = requests.get("%s/server/%d/execute/annual_water_yield/"
                         % (dashboard_url, registered_wps_server), timeout=120)
    assert plain.status_code == 200, plain.text[:1000]
    assert 'value="gura"' not in plain.text


def test_generated_form_offers_upload_and_destinations(registered_wps_server,
                                                      dashboard_url):
    """The wrapper's own inputs render as a checkbox and server pickers.

    They come from DescribeProcess like everything else, but a bare anyURI would
    render as a text box; the useful destinations are the servers already
    registered, so they are choices.
    """
    r = requests.get("%s/server/%d/execute/carbon/" % (dashboard_url,
                                                       registered_wps_server),
                     timeout=120)
    assert r.status_code == 200, r.text[:1000]
    assert re.search(r'<input type="checkbox" name="upload_results"', r.text), \
        r.text[:2000]
    for kind in ("wcs", "wfs", "http"):
        assert re.search(r'<select name="destination_%s"' % kind, r.text), kind


# The full upload round trip -- anticipated -> Local Pending -> published ->
# registered -- is not automated here. Driving it needs a *valid* job, and the
# generated form takes element ids rather than paths, so a test has to pick
# inputs that genuinely belong together or the model rightly fails. Verified by
# hand against a loaded demo: carbon with upload_results listed its anticipated
# outputs under Local Pending WCS/HTTP at Run, and on Succeeded the entries were
# cleared and results:c_*_willamette appeared on the destination source.
# Worth automating once there is a fixture that builds a known-good job.


def test_dashboard_wps_process_detail(registered_wps_server, dashboard_url):
    """Describes a process through owslib -- the path that raised
    TypeError: WebProcessingService.__init__() got an unexpected keyword
    argument 'verbose' once owslib dropped that parameter."""
    r = requests.get(
        "%s/server/WPS/%d/element/annual_water_yield/" % (dashboard_url,
                                                          registered_wps_server),
        timeout=120)
    assert r.status_code == 200, r.text[:1000]
