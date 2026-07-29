"""WPS-server smoke tests that do not require GeoServer.

Validates the generalized middleware: GetCapabilities should advertise every
importable InVEST model, DescribeProcess should render every one of those specs
(and expose the expected args for a known model), the runner-only arguments
should stay hidden, and the echo process should round-trip.
"""
import pytest
import requests
from owslib.wps import WebProcessingService

# A representative subset that must always be present in modern InVEST.
EXPECTED_MODELS = {"carbon", "annual_water_yield", "sdr", "ndr",
                   "habitat_quality", "pollination"}


def _expected_model_ids():
    """The model ids invest_models.get_processes() should expose, computed the
    same way (registry minus models that fail to import)."""
    import importlib
    from natcap.invest import model_metadata
    ids = []
    for model_id, meta in model_metadata.MODEL_METADATA.items():
        try:
            module = importlib.import_module(meta.pyname)
        except Exception:
            continue
        if hasattr(module, "MODEL_SPEC") and hasattr(module, "execute"):
            ids.append(model_id)
    return set(ids)


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
    assert "lulc_cur_path" in input_ids
    assert "carbon_pools_path" in input_ids
    assert "calc_sequestration" in input_ids


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
