"""End-to-end smoke test: run an InVEST model via WPS and publish to GeoServer.

Carbon is the lightest model with a raster output. It exercises the full generic
path: collect args -> module.execute() -> publish MODEL_SPEC outputs to GeoServer
-> return WMS URL. Requires the geoserver service to be up.
"""
import os
import re

import pytest
import requests

DATA_DIR = "/app/tests/data"
LULC = os.path.join(DATA_DIR, "lulc_willamette.tif")
POOLS = os.path.join(DATA_DIR, "carbon_pools_willamette.csv")


def test_carbon_executes_and_publishes(wps_url, geoserver_url):
    assert os.path.exists(LULC), "missing test raster %s" % LULC
    assert os.path.exists(POOLS), "missing test table %s" % POOLS

    data_inputs = ";".join([
        "lulc_bas_path=%s" % LULC,
        "carbon_pools_path=%s" % POOLS,
        "calc_sequestration=false",
    ])

    resp = requests.get(wps_url, params={
        "service": "WPS",
        "version": "1.0.0",
        "request": "Execute",
        "identifier": "carbon",
        "DataInputs": data_inputs,
    }, timeout=900)

    assert resp.status_code == 200, resp.text[:1000]
    # ProcessSucceeded implies execute() ran AND outputs published to GeoServer
    # (a publish failure would raise and surface as ProcessFailed).
    assert "ProcessSucceeded" in resp.text, resp.text[:3000]
    assert "wms" in resp.text.lower(), resp.text[:3000]


def test_every_published_layer_is_advertised_by_wms(geoserver_url):
    """A layer GeoServer will not advertise is a layer nobody can find.

    A layer imported without a resolvable CRS gets no latLonBoundingBox, and
    WMS 1.3.0 cannot emit a layer without an EX_GeographicBoundingBox -- so
    GeoServer drops it from GetCapabilities while still serving it perfectly
    over WFS and WCS. Publishing succeeds, every round-trip test passes, and
    the layer is simply undiscoverable, which is how four of the demo's layers
    stayed broken without failing anything.
    """
    auth = (os.environ.get("GEOSERVER_USER", "admin"),
            os.environ.get("GEOSERVER_PASS", "geoserver"))
    workspace = os.environ.get("DEMO_WORKSPACE", "invest")

    listing = requests.get("%s/rest/workspaces/%s/layers.json"
                           % (geoserver_url, workspace), auth=auth, timeout=60)
    if listing.status_code == 404:
        pytest.skip("needs the demo loaded (make demo): no %s workspace"
                    % workspace)
    assert listing.status_code == 200, listing.text[:500]
    published = {layer["name"] for layer
                 in listing.json().get("layers", {}).get("layer", [])}
    if not published:
        pytest.skip("needs the demo loaded (make demo): no published layers")

    caps = requests.get("%s/ows" % geoserver_url, params={
        "service": "WMS", "version": "1.3.0", "request": "GetCapabilities",
    }, timeout=120)
    assert caps.status_code == 200, caps.text[:500]
    advertised = set(re.findall(r"<Name>%s:([^<]+)</Name>" % re.escape(workspace),
                                caps.text))

    missing = sorted(published - advertised)
    assert not missing, (
        "%d of %d layers are published but not advertised by WMS, so no client "
        "can discover them: %s" % (len(missing), len(published), missing[:10]))
