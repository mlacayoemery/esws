"""WPS-server smoke tests that do not require GeoServer.

Validates the generalized middleware: GetCapabilities should advertise every
importable InVEST model, DescribeProcess should render every one of those specs
(and expose the expected args for a known model), the runner-only arguments
should stay hidden, and the echo process should round-trip.
"""
import re

import pytest
import requests
from owslib.wps import WebProcessingService

# A representative subset that must always be present in modern InVEST.
EXPECTED_MODELS = {"carbon", "annual_water_yield", "sdr", "ndr",
                   "habitat_quality", "pollination"}


def _expected_model_ids():
    """The model ids invest_models.get_processes() should expose.

    natcap.invest.models builds this registry at import time by walking the
    package and keeping every module that looks like a model, which is the same
    set the wrapper iterates.
    """
    from natcap.invest import models
    return set(models.model_id_to_pyname)


def test_getcapabilities_lists_all_invest_models(wps_url):
    wps = WebProcessingService(wps_url, version="1.0.0", skip_caps=False)
    advertised = {p.identifier for p in wps.processes}

    # The generalized wrapper must advertise the full importable registry.
    assert _expected_model_ids().issubset(advertised)
    # ... and at least the representative core models.
    assert EXPECTED_MODELS.issubset(advertised), \
        "missing: %s" % (EXPECTED_MODELS - advertised)
    # legacy + echo processes still present
    assert "echo_string" in advertised
    assert "natcap.invest.hydropower.hydropower_water_yield" in advertised


@pytest.fixture(scope="module")
def described_models(wps_url):
    """{model_id: set of input identifiers} for every advertised InVEST model.

    Describing 25 models is the expensive part, so it happens once here and the
    tests below share the result. A model that fails to describe is stored as
    its exception rather than raised, so one bad spec reports as a single test
    failure listing every offender instead of aborting the fixture.
    """
    wps = WebProcessingService(wps_url, version="1.0.0")
    described = {}
    for model_id in sorted(_expected_model_ids()):
        try:
            proc = wps.describeprocess(model_id)
            described[model_id] = {i.identifier for i in proc.dataInputs}
        except Exception as exc:  # noqa: BLE001 - asserted on below
            described[model_id] = exc
    return described


def test_describeprocess_succeeds_for_every_model(described_models):
    """GetCapabilities only proves each process got registered. MODEL_SPEC is
    not translated into WPS inputs until DescribeProcess, so a spec the wrapper
    cannot render is invisible until then -- which matters because the model
    set moves with every InVEST upgrade."""
    # Guard against a vacuous pass: an empty registry would satisfy every
    # assertion below without describing anything.
    assert len(described_models) >= 20, \
        "expected the full InVEST registry, got %d" % len(described_models)

    broken = {m: repr(r) for m, r in described_models.items()
              if isinstance(r, Exception)}
    assert not broken, "DescribeProcess failed for: %s" % broken

    empty = sorted(m for m, r in described_models.items() if not r)
    assert not empty, "no inputs advertised for: %s" % empty


def test_runner_args_hidden_but_results_suffix_exposed(described_models):
    """workspace_dir and n_workers are managed by the wrapper and must never be
    client-settable. results_suffix deliberately is -- docsrc/models.rst tells
    readers so, and this keeps that claim honest."""
    hidden = {"workspace_dir", "n_workers"}
    leaked = {m: sorted(hidden & r) for m, r in described_models.items()
              if not isinstance(r, Exception) and hidden & r}
    assert not leaked, "runner-only args exposed as WPS inputs: %s" % leaked

    missing = sorted(m for m, r in described_models.items()
                     if not isinstance(r, Exception) and "results_suffix" not in r)
    assert not missing, "results_suffix not exposed by: %s" % missing


def test_describeprocess_carbon_exposes_spec_args(wps_url):
    wps = WebProcessingService(wps_url, version="1.0.0")
    carbon = wps.describeprocess("carbon")
    input_ids = {i.identifier for i in carbon.dataInputs}
    # InVEST 3.20 renamed carbon's scenarios current/future -> baseline/alternate
    # and dropped the REDD scenario entirely.
    assert "lulc_bas_path" in input_ids
    assert "carbon_pools_path" in input_ids
    assert "calc_sequestration" in input_ids


def test_processes_declare_their_real_outputs(wps_url):
    """Every model must advertise the outputs it produces, not one blob.

    Each declared output is a ComplexOutput derived from MODEL_SPEC.outputs, so
    a client can see what it will get and request individual outputs by
    reference. `response` is retained alongside them for existing clients.
    """
    wps = WebProcessingService(wps_url, version="1.0.0")
    carbon = wps.describeprocess("carbon")
    identifiers = {o.identifier for o in carbon.processOutputs}

    assert "response" in identifiers, identifiers
    assert len(identifiers) > 5, identifiers
    # a raster the model always produces
    assert "c_storage_bas" in identifiers, sorted(identifiers)


def test_executing_returns_fetchable_output_references(wps_url):
    """A run's outputs come back as URLs that actually serve the file.

    Exercises the whole chain that was broken: pywps needs a writable
    outputpath, wpsserver has to serve it, and outputurl has to be reachable
    from outside the container.
    """
    resp = requests.get(wps_url, params={
        "service": "WPS",
        "version": "1.0.0",
        "request": "Execute",
        "identifier": "carbon",
        "DataInputs": ";".join([
            "lulc_bas_path=/data/invest/Carbon/lulc_current_willamette.tif",
            "carbon_pools_path=/data/invest/Carbon/carbon_pools_willamette.csv",
            "calc_sequestration=false",
        ]),
    }, timeout=900)
    assert resp.status_code == 200, resp.text[:1000]
    assert "ProcessSucceeded" in resp.text, resp.text[:3000]

    hrefs = [h for h in re.findall(r'href="([^"]+)"', resp.text) if h]
    assert hrefs, resp.text[:3000]

    # The advertised URL is the one external clients use (WPS_OUTPUT_URL, the
    # host mapping). These tests run on the compose network, so point it back at
    # the service instead of the published port.
    from urllib.parse import urlsplit, urlunsplit
    wps_parts = urlsplit(wps_url)
    href_parts = urlsplit(hrefs[0])
    internal = urlunsplit((wps_parts.scheme, wps_parts.netloc,
                           href_parts.path, href_parts.query, ""))

    fetched = requests.get(internal, timeout=120)
    assert fetched.status_code == 200, internal
    assert len(fetched.content) > 0, internal


def test_echo_execute_roundtrips(wps_url):
    resp = requests.get(wps_url, params={
        "service": "WPS",
        "version": "1.0.0",
        "request": "Execute",
        "identifier": "echo_string",
        "DataInputs": "message=hello-esws",
    }, timeout=30)
    assert resp.status_code == 200, resp.text[:500]
    assert "hello-esws" in resp.text
