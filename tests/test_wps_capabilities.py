"""WPS-server smoke tests that do not require GeoServer.

Validates the generalized middleware: GetCapabilities should advertise every
importable InVEST model, DescribeProcess should expose a model's MODEL_SPEC args,
and the echo process should round-trip.
"""
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
