"""GeoServer's own WPS, and chaining it onto an InVEST result.

ESWS runs InVEST behind pywps; GeoServer runs its own catalogue of ~196 spatial
processes behind its WPS extension. The two never need to speak WPS to each
other: ESWS already publishes model outputs into GeoServer's catalogue, so a
GeoServer process can take an InVEST raster as input by layer name. That is the
whole integration, and these tests are what keep it true.

Both are WPS 1.0.0 (pywps also advertises 2.0.0), so a single client drives both.
"""
import re

import pytest
import requests

# Present in the stock gt-process jars, so their absence means the WPS *service*
# extension is missing rather than any particular process being unavailable.
EXPECTED_PROCESSES = {"gs:Contour", "gs:CropCoverage", "JTS:area"}


@pytest.fixture(scope="module")
def geoserver_wps_capabilities(geoserver_url):
    resp = requests.get(geoserver_url + "/ows", params={
        "service": "WPS", "version": "1.0.0", "request": "GetCapabilities",
    }, timeout=120)
    assert resp.status_code == 200, resp.text[:500]
    return resp.text


def test_geoserver_serves_wps(geoserver_wps_capabilities):
    """The WPS extension has to be installed in the image.

    Only gt-process* (the GeoTools process *framework*) ships in the stock
    GeoServer image; the service that exposes those processes is a separate
    extension. Without it GeoServer answers this request with a ServiceException
    and every chaining test below is meaningless -- so assert the offering, not
    just a 200.
    """
    assert "<wps:ProcessOfferings>" in geoserver_wps_capabilities

    advertised = set(re.findall(r"<ows:Identifier>([^<]+)</ows:Identifier>",
                                geoserver_wps_capabilities))
    missing = EXPECTED_PROCESSES - advertised
    assert not missing, "WPS extension present but missing processes: %s" % missing

    # Guard against a vacuous pass: a capabilities document listing only the
    # three above would satisfy the assertion without the catalogue being real.
    assert len(advertised) > 100, \
        "expected GeoServer's full process catalogue, got %d" % len(advertised)


def test_both_servers_speak_wps_100(geoserver_wps_capabilities, wps_url):
    """The protocol is the thing the two sides actually share.

    GeoServer's WPS implements 1.0.0 only. pywps advertises 1.0.0 and 2.0.0, so
    the usable intersection is 1.0.0 -- if either side ever stops offering it,
    a client can no longer drive both from one code path.
    """
    assert "<ows:ServiceTypeVersion>1.0.0</ows:ServiceTypeVersion>" \
        in geoserver_wps_capabilities

    esws = requests.get(wps_url, params={
        "service": "WPS", "request": "GetCapabilities", "version": "1.0.0",
    }, timeout=60)
    assert esws.status_code == 200, esws.text[:500]
    assert "<ows:ServiceTypeVersion>1.0.0</ows:ServiceTypeVersion>" in esws.text


@pytest.fixture(scope="module")
def published_carbon_layer(wps_url, geoserver_url):
    """Run carbon with upload_results and return its published "ws:layer".

    The published raster is the hand-off point between the two servers, so the
    chaining test needs a real one rather than a fixture layer.
    """
    resp = requests.get(wps_url, params={
        "service": "WPS",
        "version": "1.0.0",
        "request": "Execute",
        "identifier": "carbon",
        "DataInputs": ";".join([
            "lulc_bas_path=/app/tests/data/lulc_willamette.tif",
            "carbon_pools_path=/app/tests/data/carbon_pools_willamette.csv",
            "calc_sequestration=false",
            "upload_results=true",
        ]),
    }, timeout=900)
    assert resp.status_code == 200, resp.text[:1000]
    assert "ProcessSucceeded" in resp.text, resp.text[:3000]

    published = re.search(r"layers=([\w.\-]+:[\w.\-]+)", resp.text)
    assert published, "no published layer in the response: %s" % resp.text[:3000]
    return published.group(1)


def test_a_geoserver_process_consumes_an_invest_output(published_carbon_layer,
                                                       geoserver_url):
    """The integration, end to end: gs:Contour over InVEST's carbon raster.

    No bridge, no adapter and no second protocol hop -- the raster is addressed
    by the catalogue name ESWS published it under, and GeoServer resolves it
    internally via the xlink:href="http://geoserver/wcs" shortcut.

    Streamed and read in a bounded prefix on purpose: contouring a full-
    resolution carbon raster at a fine interval produces hundreds of thousands
    of features (~400MB of GeoJSON at interval=25), which is worth knowing
    before anyone wires this into a UI, but is not worth downloading here.
    """
    workspace, layer = published_carbon_layer.split(":", 1)
    execute = """<?xml version="1.0" encoding="UTF-8"?>
<wps:Execute version="1.0.0" service="WPS"
             xmlns:wps="http://www.opengis.net/wps/1.0.0"
             xmlns:ows="http://www.opengis.net/ows/1.1"
             xmlns:wcs="http://www.opengis.net/wcs/2.0"
             xmlns:xlink="http://www.w3.org/1999/xlink">
  <ows:Identifier>gs:Contour</ows:Identifier>
  <wps:DataInputs>
    <wps:Input>
      <ows:Identifier>data</ows:Identifier>
      <wps:Reference mimeType="image/tiff" xlink:href="http://geoserver/wcs"
                     method="POST">
        <wps:Body>
          <wcs:GetCoverage service="WCS" version="2.0.1">
            <wcs:CoverageId>%s__%s</wcs:CoverageId>
            <wcs:format>image/tiff</wcs:format>
          </wcs:GetCoverage>
        </wps:Body>
      </wps:Reference>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>interval</ows:Identifier>
      <wps:Data><wps:LiteralData>100</wps:LiteralData></wps:Data>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>simplify</ows:Identifier>
      <wps:Data><wps:LiteralData>true</wps:LiteralData></wps:Data>
    </wps:Input>
  </wps:DataInputs>
  <wps:ResponseForm>
    <wps:RawDataOutput mimeType="application/json">
      <ows:Identifier>result</ows:Identifier>
    </wps:RawDataOutput>
  </wps:ResponseForm>
</wps:Execute>""" % (workspace, layer)

    with requests.post(geoserver_url + "/ows", data=execute.encode("utf-8"),
                       headers={"Content-Type": "text/xml"},
                       stream=True, timeout=900) as resp:
        assert resp.status_code == 200, resp.text[:1000]
        head = resp.raw.read(65536, decode_content=True).decode("utf-8", "replace")

    # A ServiceException also comes back 200 from GeoServer's OWS dispatcher, so
    # the body is the only thing that distinguishes success from failure.
    assert "ExceptionReport" not in head, head[:1000]
    assert '"type":"FeatureCollection"' in head, head[:1000]
    assert '"type":"Feature"' in head, head[:1000]

    # Contour values come from the InVEST raster's own carbon-storage values, so
    # a plausible one proves the coverage really was read rather than an empty
    # collection returned.
    values = [float(v) for v in re.findall(r'"value":([0-9.]+)', head)]
    assert values, head[:1000]
    assert all(v % 100 == 0 for v in values), sorted(set(values))[:10]
