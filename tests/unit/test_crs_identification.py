"""Unit tests for CRS identification (tools/crs_identify.py).

Stack-free: these check the rules on WKT strings directly, which is where the
judgements live -- what may be assumed about a missing datum, and what may not.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "tools"))

pytest.importorskip("pyproj")
import crs_identify  # noqa: E402
from pyproj import CRS  # noqa: E402

# InVEST's Brazilian samples: UTM zone 21S stated in full, datum left unnamed.
UTM21S_NO_DATUM = (
    'PROJCS["Transverse_Mercator",GEOGCS["GCS_unnamed ellipse",'
    'DATUM["D_unknown",SPHEROID["Unknown",6378137,298.257222101]],'
    'PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],'
    'PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],'
    'PARAMETER["central_meridian",-57],PARAMETER["scale_factor",0.9996],'
    'PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],'
    'UNIT["Meter",1]]')

# NASA's own definition, published verbatim in the LP DAAC user guides.
MODIS_SINUSOIDAL = (
    'PROJCS["Sinusoidal",GEOGCS["GCS_unnamed ellipse",DATUM["D_unknown",'
    'SPHEROID["Unknown",6371007.181,0]],PRIMEM["Greenwich",0],'
    'UNIT["Degree",0.017453292519943295]],PROJECTION["Sinusoidal"],'
    'PARAMETER["central_meridian",0],PARAMETER["false_easting",0],'
    'PARAMETER["false_northing",0],UNIT["Meter",1]]')

# The same projection on an ellipsoid whose datum genuinely differs: SAD69 is
# 60 m from SIRGAS 2000 in this region.
UTM21S_INTL1924 = UTM21S_NO_DATUM.replace("6378137,298.257222101",
                                          "6378388,297.0")


def test_a_missing_datum_on_grs80_is_read_as_wgs84():
    """The projection is fully determined; only the datum's name is absent, and
    every modern datum on this ellipsoid agrees to about a metre."""
    code = crs_identify._wgs84_equivalent(CRS.from_wkt(UTM21S_NO_DATUM), 90,
                                     crs_identify.logging.getLogger("t"))
    assert code == "EPSG:32721", code


def test_a_missing_datum_on_an_older_ellipsoid_is_refused():
    """International 1924 means the datum really does differ -- assuming WGS 84
    would move the data tens of metres."""
    assert crs_identify._wgs84_equivalent(CRS.from_wkt(UTM21S_INTL1924), 90,
                                     crs_identify.logging.getLogger("t")) is None


def test_a_named_datum_is_never_overridden():
    named = CRS.from_epsg(31981)  # SIRGAS 2000 / UTM 21S
    assert crs_identify._wgs84_equivalent(named, 90,
                                     crs_identify.logging.getLogger("t")) is None


def test_the_modis_sphere_is_recognised_rather_than_guessed():
    code, name = crs_identify._vendor_code(CRS.from_wkt(MODIS_SINUSOIDAL))
    assert name == "MODIS Sinusoidal"
    # Not EPSG:6842: that code is assigned to NAD83(2011) / Oregon Coast zone,
    # and registering it would serve this data under a .prj from the wrong side
    # of the planet.
    assert code == "EPSG:996842", code
    assert CRS.from_epsg(6842).name == "NAD83(2011) / Oregon Coast zone (m)"


def test_the_modis_sphere_is_not_read_as_wgs84():
    """A sphere is not the GRS 80 ellipsoid, so the datum fallback must decline
    even though the datum is equally unnamed."""
    assert crs_identify._wgs84_equivalent(CRS.from_wkt(MODIS_SINUSOIDAL), 90,
                                     crs_identify.logging.getLogger("t")) is None


def test_projection_equality_compares_parameters_not_names():
    assert crs_identify._same_projection(CRS.from_epsg(32721), CRS.from_epsg(31981))
    assert not crs_identify._same_projection(CRS.from_epsg(32721), CRS.from_epsg(32722))


def test_an_unresolvable_authority_is_dropped_from_a_prj(tmp_path):
    """GeoServer labels a layer with the private code it was published under;
    PROJ resolves the authority first and fails instead of reading the WKT."""
    prj = tmp_path / "layer.prj"
    prj.write_text(MODIS_SINUSOIDAL[:-1] + ',AUTHORITY["EPSG","996842"]]')
    crs_identify.drop_unresolvable_authority(str(tmp_path),
                                        crs_identify.logging.getLogger("t"))
    cleaned = prj.read_text()
    assert "AUTHORITY" not in cleaned, cleaned
    assert CRS.from_wkt(cleaned).ellipsoid.semi_major_metre == 6371007.181


def test_a_resolvable_authority_is_left_alone(tmp_path):
    prj = tmp_path / "layer.prj"
    original = CRS.from_epsg(32721).to_wkt("WKT1_GDAL")
    prj.write_text(original)
    crs_identify.drop_unresolvable_authority(str(tmp_path),
                                        crs_identify.logging.getLogger("t"))
    assert prj.read_text() == original


def test_the_shipped_geoserver_definitions_parse_and_are_what_they_claim():
    """A typo in docker/geoserver/epsg.properties would not fail loudly.

    GeoServer would decline the definition and go back to publishing those layers
    disabled -- the state this file exists to fix -- so the file is checked here
    rather than only in an integration run.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "docker", "geoserver", "epsg.properties")
    entries = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#"):
            code, _, wkt = line.partition("=")
            entries[code] = wkt

    assert "996842" in entries, sorted(entries)
    # Not 6842: that is NAD83(2011) / Oregon Coast zone, and this file extends the
    # EPSG namespace, so registering it there is silently ignored in favour of the
    # real definition.
    assert "6842" not in entries, "6842 collides with an assigned EPSG code"

    crs = CRS.from_wkt(entries["996842"])
    assert "sinusoidal" in crs.coordinate_operation.method_name.lower()
    assert crs.ellipsoid.semi_major_metre == 6371007.181
    # The vendor table has to point at the code that is actually registered.
    assert crs_identify._VENDOR_CRS[0]["code"] == "EPSG:996842"
