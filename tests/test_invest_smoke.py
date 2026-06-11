"""End-to-end smoke test: run an InVEST model via WPS and publish to GeoServer.

Carbon is the lightest model with a raster output. It exercises the full generic
path: collect args -> module.execute() -> publish MODEL_SPEC outputs to GeoServer
-> return WMS URL. Requires the geoserver service to be up.
"""
import os

import requests

DATA_DIR = "/app/tests/data"
LULC = os.path.join(DATA_DIR, "lulc_willamette.tif")
POOLS = os.path.join(DATA_DIR, "carbon_pools_willamette.csv")


def test_carbon_executes_and_publishes(wps_url, geoserver_url):
    assert os.path.exists(LULC), "missing test raster %s" % LULC
    assert os.path.exists(POOLS), "missing test table %s" % POOLS

    data_inputs = ";".join([
        "lulc_cur_path=%s" % LULC,
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
