"""Django dashboard smoke tests — key views return 200 on the pinned Django."""
import html
import os
import re
import time
from urllib.parse import quote

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
    kwarg survived the Django port unnoticed.

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


def _pending_counts(session, dashboard_url, job_pk):
    """{server type: entries for this job} across the Local Pending sources."""
    counts = {}
    for server_type in ("WCS", "WFS", "CSV"):
        listing = session.get("%s/server/%s/" % (dashboard_url, server_type),
                              timeout=60).text
        for row in re.findall(r"<tr>(.*?)</tr>", listing, re.S):
            if "Local Pending" not in row:
                continue
            pk = re.search(r"<td>(\d+)</td>", row).group(1)
            elements = session.get("%s/server/%s/%s/element/"
                                   % (dashboard_url, server_type, pk),
                                   timeout=60).text
            counts[server_type] = len(re.findall(r"job%d:" % job_pk, elements))
    return counts


def _write_shared_table(relative_path, content):
    """Write a table into the volume the file server publishes.

    The tests run inside the same image as the wps service and share that volume,
    so the file appears under the file server's /results/ without shelling out.
    """
    path = os.path.join("/app/data", relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write(content)


def _demo_template_pk(dashboard_url):
    """The pk of the demo Templates source, or None if the demo is not loaded."""
    templates = requests.get(dashboard_url + "/server/TPL/", timeout=30).text
    template_pk = None
    for row in re.findall(r"<tr>(.*?)</tr>", templates, re.S):
        if "InVEST Demo" not in row:
            continue
        # The title is a plain cell; the row's own element link carries the pk.
        found = re.search(r"/server/TPL/(\d+)/element/", row)
        if found:
            template_pk = int(found.group(1))
    return template_pk


def _submit_template_job(session, dashboard_url, template_pk, process_id,
                         extra=None):
    """Fill a template's job form with its own prefilled values and submit it.

    Returns (job_pk, {destination field: server pk}). The prefilled values are
    InVEST's sample arguments; picking an arbitrary option per dropdown instead
    would build a job that is valid to Django and nonsense to InVEST.
    """
    form_url = "%s/server/%d/execute/%s/" % (dashboard_url, template_pk, process_id)
    page = session.get(form_url, timeout=180).text
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)

    data = {"csrfmiddlewaretoken": token, "upload_results": "on"}
    destinations = {}
    for match in re.finditer(r'<select name="([a-z_]+)"(.*?)</select>', page, re.S):
        name, body = match.group(1), match.group(2)
        if name.startswith("destination_"):
            option = re.search(r'<option value="(\d+)">', body)
            if option:
                destinations[name] = option.group(1)
            continue
        chosen = re.search(r'<option value="(\d+)" selected>', body)
        if chosen:
            data[name] = chosen.group(1)
    assert len(destinations) == 3, destinations
    data.update(destinations)

    for match in re.finditer(r'<input type="[a-z]+" name="([a-z_]+)"[^>]*value="([^"]*)"',
                             page):
        if match.group(1) != "csrfmiddlewaretoken" and match.group(2):
            data.setdefault(match.group(1), match.group(2))

    # Last, so an explicit override wins over the prefilled value it replaces.
    data.update(extra or {})

    posted = session.post(form_url, data=data, headers={"Referer": form_url},
                          timeout=300)
    assert posted.status_code == 200, posted.text[:1000]
    job = re.search(r"/job/(\d+)/", posted.url)
    assert job, "form did not validate: %s" % posted.url
    return int(job.group(1)), destinations


def _await_job(session, dashboard_url, job_pk, tries=60):
    """Poll a job to completion, returning the final status page."""
    status = ""
    for _ in range(tries):
        status = session.get("%s/job/%d/status/" % (dashboard_url, job_pk),
                             timeout=180).text
        state = re.search(r"<b>Status: </b>([A-Za-z]+)", status)
        if state and state.group(1) in ("Succeeded", "Failed"):
            return state.group(1), status
        time.sleep(4)
    return None, status


def test_upload_round_trip_moves_outputs_to_their_destinations(dashboard_url):
    """anticipated -> Local Pending -> published -> registered, for all three kinds.

    Driven through the Templates source so the model arguments are InVEST's own
    sample set: the form takes element ids, and picking an arbitrary option per
    dropdown builds a job that is valid to Django and nonsense to InVEST, which
    then rightly fails.

    annual_water_yield rather than carbon because it emits rasters, vectors and
    tables, so every destination kind is exercised in one run.
    """
    template_pk = _demo_template_pk(dashboard_url)
    if template_pk is None:
        pytest.skip("needs the demo loaded (make demo): no InVEST Demo template")

    session = requests.Session()
    job_pk, destinations = _submit_template_job(session, dashboard_url, template_pk,
                                                "annual_water_yield")

    session.get("%s/job/%d/run/" % (dashboard_url, job_pk), timeout=180)

    listed = _pending_counts(session, dashboard_url, job_pk)
    assert listed.get("WCS"), listed
    assert listed.get("WFS"), listed
    assert listed.get("CSV"), listed

    state, status = _await_job(session, dashboard_url, job_pk)
    assert state == "Succeeded", status[:2000]

    # Every pending entry for this job is gone...
    cleared = _pending_counts(session, dashboard_url, job_pk)
    assert not any(cleared.values()), cleared

    # What the WPS says it published. Reported on failure below so a miss reads as
    # "the server published nothing" or "published but the client did not
    # register it" without digging through the server log.
    # The status page embeds the ExecuteResponse as escaped markup, so unescape
    # before matching -- searching the raw HTML for <wps:LiteralData never hits.
    reported = re.search(r"uploaded</ows:Identifier>.*?<wps:LiteralData[^>]*>"
                         r"([^<]*)</wps:LiteralData>", html.unescape(status), re.S)
    reported = reported.group(1).strip() if reported else "<no uploaded output>"

    # ...and the results are registered against the chosen destinations.
    registered = {}
    for field, server_type, expected in (
            ("destination_wcs", "WCS", "results:fractp"),
            ("destination_wfs", "WFS", "results:watershed_results_wyield"),
            ("destination_http", "CSV", "results/watershed_results_wyield")):
        elements = session.get("%s/server/%s/%s/element/"
                               % (dashboard_url, server_type, destinations[field]),
                               timeout=120).text
        assert expected in elements, (server_type, expected, reported)
        registered[server_type] = elements

    # Results only: the model writes ten more rasters under intermediate/, and
    # publishing those buried the results the run was actually for. Scoped to the
    # results workspace -- the demo publishes its *inputs* to the same GeoServer,
    # so bare names like eto appear in the listing either way.
    for intermediate in ("clipped_lulc", "eto", "kc_raster", "depth_to_root"):
        assert "results:%s" % intermediate not in registered["WCS"], intermediate

    # The table is a genuine upload, not a pointer at where it already sat: it
    # is fetchable from the file server it was registered against.
    table = re.search(r"results/[A-Za-z0-9_]+\.csv", registered["CSV"]).group(0)
    fetched = requests.get("%s/%s" % (os.environ.get(
        "FILESERVER_URL", "http://localhost:8001"), table), timeout=60)
    assert fetched.status_code == 200, fetched.status_code
    assert fetched.text.splitlines()[0].count(",") >= 1, fetched.text[:200]


def test_dashboard_wps_process_detail(registered_wps_server, dashboard_url):
    """Describes a process through owslib -- the path that raised
    TypeError: WebProcessingService.__init__() got an unexpected keyword
    argument 'verbose' once owslib dropped that parameter."""
    r = requests.get(
        "%s/server/WPS/%d/element/annual_water_yield/" % (dashboard_url,
                                                          registered_wps_server),
        timeout=120)
    assert r.status_code == 200, r.text[:1000]


def test_generated_form_enforces_the_declared_range(registered_wps_server,
                                                    dashboard_url):
    """A value the model would reject is rejected by the form.

    forest_carbon_edge_effect's conversion factor is a ratio, so 1.5 is out of
    range; annual_water_yield's seasonality constant must exceed 0, so 0 is too.
    Both bounds come from the WPS, not from anything hard-coded here.
    """
    ratio = requests.get("%s/server/%d/execute/forest_carbon_edge_effect/"
                         % (dashboard_url, registered_wps_server), timeout=120)
    assert ratio.status_code == 200, ratio.text[:1000]
    field = re.search(r'<input[^>]*name="biomass_to_carbon_conversion_factor"[^>]*>',
                      ratio.text)
    assert field, ratio.text[:2000]
    assert 'min="0.0"' in field.group(0), field.group(0)
    assert 'max="1.0"' in field.group(0), field.group(0)

    # An exclusive bound has no HTML equivalent, so it is nudged one step: the
    # smallest accepted value is just above 0, not 0 itself.
    exclusive = requests.get("%s/server/%d/execute/annual_water_yield/"
                             % (dashboard_url, registered_wps_server), timeout=120)
    field = re.search(r'<input[^>]*name="seasonality_constant"[^>]*>',
                      exclusive.text)
    assert field, exclusive.text[:2000]
    assert 'min="1e-09"' in field.group(0), field.group(0)


def test_unique_run_does_not_overwrite_the_previous_runs_outputs(dashboard_url):
    """Running a job twice with the flag set leaves both runs' results in place.

    Output filenames -- and so the layer names they are published under -- derive
    from results_suffix, so without a per-run token the second run republishes
    over the first. With the flag, each run adds its own token and both sets of
    layers survive.
    """
    template_pk = _demo_template_pk(dashboard_url)
    if template_pk is None:
        pytest.skip("needs the demo loaded (make demo): no InVEST Demo template")

    session = requests.Session()
    job_pk, destinations = _submit_template_job(
        session, dashboard_url, template_pk, "annual_water_yield",
        extra={"esws_unique_run": "on"})

    detail = session.get("%s/job/%d/" % (dashboard_url, job_pk), timeout=60).text
    assert "esws:unique_run" in detail, detail[:2000]

    def wyield_layers():
        elements = session.get("%s/server/WCS/%s/element/"
                               % (dashboard_url, destinations["destination_wcs"]),
                               timeout=120).text
        return set(re.findall(r"results:(wyield_[A-Za-z0-9_]+)", elements))

    # Measured as a delta: other tests publish to the same destination.
    before = wyield_layers()
    session.get("%s/job/%d/run/" % (dashboard_url, job_pk), timeout=180)
    state, status = _await_job(session, dashboard_url, job_pk)
    assert state == "Succeeded", status[:2000]
    first = wyield_layers()
    assert len(first - before) == 1, (before, first)

    # "Run Again" is its own action: job_run on a finished job is the status poll.
    assert "/job/%d/rerun/" % job_pk in session.get(
        "%s/job/%d/" % (dashboard_url, job_pk), timeout=60).text
    session.get("%s/job/%d/rerun/" % (dashboard_url, job_pk), timeout=180)
    state, status = _await_job(session, dashboard_url, job_pk)
    assert state == "Succeeded", status[:2000]

    second = wyield_layers()
    assert first < second, (first, second)
    assert len(second - before) == 2, (before, second)


def test_change_detection_distinguishes_changed_from_unchanged(dashboard_url):
    """Fingerprint a table, rewrite it, and see only that one reported changed.

    Uses the writable results share, since the sample data is mounted read-only:
    a check has to be able to observe an actual change, not just run.
    """
    if _demo_template_pk(dashboard_url) is None:
        pytest.skip("needs the demo loaded (make demo): no registered sources")

    servers = requests.get(dashboard_url + "/server/CSV/", timeout=30).text
    pk = None
    for row in re.findall(r"<tr>(.*?)</tr>", servers, re.S):
        if "Local Pending" in row:
            continue
        found = re.search(r"/server/CSV/(\d+)/element/", row)
        if found:
            pk = int(found.group(1))
    assert pk, servers[:1000]

    def check():
        page = requests.get("%s/server/CSV/%d/check/" % (dashboard_url, pk),
                            timeout=900).text
        tally = dict(zip(("changed", "unchanged", "unreachable"),
                         (int(n) for n in re.findall(
                             r"<td>(?:Changed|Unchanged|Unreachable)</td>"
                             r'<td align="right">(\d+)</td>', page))))
        return tally, page

    probe = "results/change_probe_test.csv"
    _write_shared_table(probe, "lucode,root_depth\n1,1000\n")
    requests.get("%s/server/CSV/%d/register/%s/"
                 % (dashboard_url, pk, quote(probe, safe="")), timeout=60)

    first, _ = check()
    assert first["changed"] == 0, first        # a first fingerprint is not a change
    assert first["unchanged"] >= 1, first

    _write_shared_table(probe, "lucode,root_depth\n1,2000\n2,500\n")
    second, page = check()
    assert second["changed"] == 1, (second, page[:1500])
    assert probe in page, page[:1500]

    # And nothing changes when nothing changes.
    third, _ = check()
    assert third["changed"] == 0, third


def test_change_detection_reports_unreachable_rather_than_unchanged(dashboard_url):
    """Two of the demo's rasters have no CRS GeoServer can serve, so they cannot
    be fingerprinted -- and must not be counted as unchanged."""
    if _demo_template_pk(dashboard_url) is None:
        pytest.skip("needs the demo loaded (make demo): no registered sources")

    servers = requests.get(dashboard_url + "/server/WCS/", timeout=30).text
    pk = None
    for row in re.findall(r"<tr>(.*?)</tr>", servers, re.S):
        if "Local Pending" in row:
            continue
        found = re.search(r"/server/WCS/(\d+)/element/", row)
        if found:
            pk = int(found.group(1))
    assert pk, servers[:1000]

    page = requests.get("%s/server/WCS/%d/check/" % (dashboard_url, pk),
                        timeout=1800).text
    counts = [int(n) for n in re.findall(
        r"<td>(?:Changed|Unchanged|Unreachable)</td><td align="
        r'"right">(\d+)</td>', page)]
    changed, unchanged, unreachable = counts
    assert unchanged > 0, page[:1500]
    assert unreachable == 2, (counts, page[:2000])
    assert changed == 0, (counts, page[:2000])


def test_a_reactive_job_reruns_when_its_input_changes(dashboard_url):
    """The whole point of #3: change the data a finished job used, and it runs again.

    The job is pointed at a copy of one of its own sample tables, placed on the
    writable share, because the sample data is mounted read-only and a job whose
    inputs cannot change cannot demonstrate reacting to a change.
    """
    template_pk = _demo_template_pk(dashboard_url)
    if template_pk is None:
        pytest.skip("needs the demo loaded (make demo): no InVEST Demo template")

    session = requests.Session()

    # A copy of the model's own biophysical table, so the run is still valid.
    # Fetched over HTTP rather than read from disk: the samples are mounted at
    # different paths in the wps and fileserver containers.
    fileserver = os.environ.get("FILESERVER_URL", "http://localhost:8001")
    source = requests.get(
        fileserver + "/invest/Annual_Water_Yield/biophysical_table_gura.csv",
        timeout=60)
    assert source.status_code == 200, source.status_code
    original = source.text
    probe = "results/reactive_biophysical.csv"
    _write_shared_table(probe, original)

    csv_servers = requests.get(dashboard_url + "/server/CSV/", timeout=30).text
    csv_pk = None
    for row in re.findall(r"<tr>(.*?)</tr>", csv_servers, re.S):
        if "Local Pending" in row:
            continue
        found = re.search(r"/server/CSV/(\d+)/element/", row)
        if found:
            csv_pk = int(found.group(1))
    assert csv_pk, csv_servers[:1000]
    session.get("%s/server/CSV/%d/register/%s/"
                % (dashboard_url, csv_pk, quote(probe, safe="")), timeout=60)

    # Fingerprint it now, so the baseline is this content. Without it a rerun of
    # this test would compare against the modified copy the last one left behind
    # and see a change before anything had changed.
    session.get("%s/server/CSV/%d/check/" % (dashboard_url, csv_pk), timeout=900)

    # Which option in the form corresponds to that element.
    form_url = "%s/server/%d/execute/annual_water_yield/" % (dashboard_url, template_pk)
    page = session.get(form_url, timeout=180).text
    select = re.search(r'<select name="biophysical_table_path"(.*?)</select>',
                       page, re.S).group(1)
    option = re.search(r'<option value="(\d+)">[^<]*%s' % re.escape(probe), select)
    assert option, select[:1500]

    job_pk, _destinations = _submit_template_job(
        session, dashboard_url, template_pk, "annual_water_yield",
        extra={"esws_reactive": "on", "esws_unique_run": "on",
               "biophysical_table_path": option.group(1)})

    session.get("%s/job/%d/run/" % (dashboard_url, job_pk), timeout=180)
    state, status = _await_job(session, dashboard_url, job_pk)
    assert state == "Succeeded", status[:2000]

    def run_token():
        """The per-run token from the job's arguments, which a rerun rotates."""
        detail = session.get("%s/job/%d/" % (dashboard_url, job_pk), timeout=60).text
        found = re.search(r"esws:run_token</td><td>([0-9a-f]+)", detail)
        return found.group(1) if found else None

    before = run_token()
    assert before, "the job did not record a run token"

    # Nothing has changed yet, so nothing should be re-run.
    quiet = session.get("%s/job/%d/react/" % (dashboard_url, job_pk), timeout=900).text
    assert "unchanged" in quiet, quiet[:1500]
    assert run_token() == before, "an unchanged input triggered a rerun"

    # Change the table the job used; now it should run again. Edited in the
    # description column, which the model does not read, so the rerun is still a
    # valid run -- the point is that the data differs, not that it is broken.
    changed_table = original.replace("Urban and paved roads",
                                     "Urban and paved roads (revised)", 1)
    assert changed_table != original, original[:200]
    _write_shared_table(probe, changed_table)
    reacted = session.get("%s/job/%d/react/" % (dashboard_url, job_pk),
                          timeout=900, allow_redirects=True)
    assert reacted.status_code == 200, reacted.status_code
    # A rerun rotates the token, which is what distinguishes it from a no-op.
    assert run_token() != before, "the changed input did not trigger a rerun"

    state, status = _await_job(session, dashboard_url, job_pk)
    assert state == "Succeeded", status[:2000]

    # The sweep across all reactive jobs must also work, and find nothing now.
    everything = session.get(dashboard_url + "/job/react/", timeout=1800).text
    assert "unchanged" in everything, everything[:1500]
