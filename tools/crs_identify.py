"""Naming a dataset's CRS well enough for GeoServer to serve it.

GeoServer leaves a layer disabled -- and so unservable, "Could not locate
coverage", "defaultCRS should not be null" -- whenever it cannot resolve the
native CRS to an authority code. That happens more often than it should with real
data: ESRI-style WKT names (RGF93_Lambert_93), definitions tagged against a
non-EPSG authority (IGNF:LAMB93 for what is plainly EPSG:2154), vendor grids with
no code at all, and files that state a projection but never name a datum.

Kept free of the GeoServer client so the rules can be exercised on their own; GDAL
is imported lazily so that reading a WKT needs only pyproj.
"""
import logging
import os
import re

logger = logging.getLogger("crs_identify")


# Semi-major axis shared by GRS 1980 and WGS 84; they differ only in flattening.
_GRS80_WGS84_A = 6378137.0
_GRS80_WGS84_RF = 298.2572

# CRSs that are published without an authority code. GeoServer cannot serve a
# layer whose CRS it cannot name, so these are declared against a private code
# registered in its user_projections (docker/geoserver/epsg.properties).
_VENDOR_CRS = (
    # MODIS sinusoidal. NASA publishes this definition verbatim in the LP DAAC
    # product user guides -- DATUM["D_unknown"] and all -- so a file carrying it
    # is complete, not damaged. It has no EPSG code and never has: a spherical
    # projection referenced to WGS 84 is not something the EPSG model expresses.
    # SR-ORG:6842 is the long-standing convention for it, from the retired
    # SR-ORG namespace on spatialreference.org, where it was titled "MODIS
    # Sinusoidal". It is registered here as 996842, not 6842: GeoServer's
    # user_projections extends the EPSG namespace, and EPSG:6842 is taken by
    # NAD83(2011) / Oregon Coast zone. See docker/geoserver/epsg.properties.
    {"method": "Sinusoidal", "semi_major": 6371007.181,
     "code": "EPSG:996842", "name": "MODIS Sinusoidal"},
)


def _crs_of(path, logger):
    """The pyproj CRS of a raster or vector, or None."""
    from osgeo import gdal
    from pyproj import CRS

    try:
        dataset = gdal.OpenEx(path)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not open %s to identify its CRS: %s" % (path, exc))
        return None
    if dataset is None:
        return None

    srs = dataset.GetSpatialRef()
    if srs is None and dataset.GetLayerCount():
        # A vector carries its CRS on the layer, not on the dataset.
        srs = dataset.GetLayer(0).GetSpatialRef()
    if srs is None:
        return None
    try:
        return CRS.from_wkt(srs.ExportToWkt())
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read the CRS of %s: %s" % (path, exc))
        return None


def _vendor_code(crs):
    """A private code for a CRS a vendor ships without one, or None."""
    operation = crs.coordinate_operation
    ellipsoid = crs.ellipsoid
    if operation is None or ellipsoid is None:
        return None, None
    for entry in _VENDOR_CRS:
        if entry["method"].lower() not in (operation.method_name or "").lower():
            continue
        if abs((ellipsoid.semi_major_metre or 0) - entry["semi_major"]) > 0.01:
            continue
        return entry["code"], entry["name"]
    return None, None


def _same_projection(one, other, tolerance=1e-6):
    """Whether two CRSs project identically: same method, same parameters."""
    a, b = one.coordinate_operation, other.coordinate_operation
    if a is None or b is None:
        return False
    if (a.method_name or "").lower() != (b.method_name or "").lower():
        return False
    values = {p.name.lower(): p.value for p in a.params}
    against = {p.name.lower(): p.value for p in b.params}
    if set(values) != set(against):
        return False
    return all(abs(values[k] - against[k]) <= tolerance for k in values)


def _wgs84_equivalent(crs, min_confidence, logger):
    """The EPSG code for this projection read on a WGS 84 datum, or None.

    A file can state its projection completely and still name no datum. InVEST's
    Brazilian samples say Transverse Mercator with UTM zone 21S parameters on a
    GRS 1980 ellipsoid, and then DATUM["D_unknown"] -- which GeoServer will not
    serve. The datum is genuinely absent rather than merely unlabelled: 230
    datums share GRS 1980, and nothing in the file distinguishes them.

    It does not matter for placement. Every modern datum built on GRS 1980 or
    WGS 84 is geocentric and they agree to within about two metres, so reading
    the projection on WGS 84 puts the data where it belongs even though it does
    not name the datum the author had in mind. (For these samples that is SIRGAS
    2000, EPSG:31981, Brazil's official system -- identical to WGS 84 here to
    within the 1 m accuracy EPSG publishes for the transformation.)

    Restricted to those two ellipsoids on purpose: a sphere, or an older
    ellipsoid such as SAD69's International 1924, means the datum really does
    differ and assuming WGS 84 would move the data tens of metres.
    """
    from pyproj import CRS

    datum = crs.datum
    name = (getattr(datum, "name", "") or "").lower()
    if datum is not None and not any(
            word in name for word in ("unknown", "undefined", "unnamed")):
        return None  # it names a datum; overriding it is not ours to do

    ellipsoid = crs.ellipsoid
    if ellipsoid is None:
        return None
    if abs((ellipsoid.semi_major_metre or 0) - _GRS80_WGS84_A) > 1e-3:
        return None
    if abs((ellipsoid.inverse_flattening or 0) - _GRS80_WGS84_RF) > 1e-3:
        return None

    parameters = crs.to_dict()
    for key in ("ellps", "a", "b", "rf", "f", "R", "towgs84", "nadgrids", "datum"):
        parameters.pop(key, None)
    parameters["datum"] = "WGS84"
    try:
        # A lower bar than naming the CRS outright, because the score here is
        # about whether pyproj recognises the parameter set as a named zone --
        # a UTM zone spelled out as a Transverse Mercator does not score highly.
        # What makes that safe is the check below, not the threshold.
        code = CRS.from_dict(parameters).to_epsg(min_confidence=70)
        if not code:
            return None
        candidate = CRS.from_epsg(code)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read %s on WGS 84: %s" % (crs.name, exc))
        return None

    # Accept it only if it projects identically. Whatever pyproj proposes, a
    # candidate whose parameters differ from the file's would move the data,
    # which is the one outcome worth refusing outright.
    if not _same_projection(crs, candidate):
        logger.debug("EPSG:%s does not project %s identically; not declaring it"
                     % (code, crs.name))
        return None
    return "EPSG:%s" % code


def identify_epsg(path, min_confidence=90, logger=logger):
    """A CRS code GeoServer can serve this file under, or None.

    GeoServer leaves a layer disabled -- and so unservable, "Could not locate
    coverage", "defaultCRS should not be null" -- whenever it cannot resolve the
    native CRS to an authority code. That happens for ESRI-style WKT names such
    as RGF93_Lambert_93, for definitions tagged against a non-EPSG authority such
    as IGNF:LAMB93, and for files that state a projection but no datum.

    Three routes, in order of how much is being assumed:

    1. pyproj names the CRS outright. It does the matching rather than
       osr.FindMatches, which only ever returns the authority a definition is
       already tagged with -- it answers IGNF:LAMB93 for a shapefile whose EPSG
       equivalent is plainly 2154.
    2. The CRS is one a vendor publishes without a code (see _VENDOR_CRS).
    3. The projection is fully determined and only the datum is missing, on an
       ellipsoid where that cannot matter (see _wgs84_equivalent).

    Returns None rather than a guess when none of those apply.
    """
    crs = _crs_of(path, logger)
    if crs is None:
        return None

    try:
        code = crs.to_epsg(min_confidence=min_confidence)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not match the CRS of %s: %s" % (path, exc))
        code = None
    if code:
        return "EPSG:%s" % code

    code, name = _vendor_code(crs)
    if code:
        logger.info("%s carries %s, which has no EPSG code; declaring %s"
                    % (os.path.basename(path), name, code))
        return code

    return _wgs84_equivalent(crs, min_confidence, logger)


def describe_crs(path, logger=logger):
    """A short description of a file's CRS, for reporting one we cannot name."""
    crs = _crs_of(path, logger)
    if crs is None:
        return "no CRS"
    operation = crs.coordinate_operation
    ellipsoid = crs.ellipsoid
    return "%s on %s (a=%s)" % (
        (operation.method_name if operation else crs.name) or "unknown projection",
        (getattr(crs.datum, "name", None) or "an unnamed datum"),
        ellipsoid.semi_major_metre if ellipsoid else "?")


def drop_unresolvable_authority(directory, logger=logger):
    """Strip an AUTHORITY reference PROJ cannot resolve from any .prj in a
    directory, keeping the definition itself.

    GeoServer labels a served layer with whatever code it was published under,
    including a private one from user_projections -- 996842 for the MODIS
    sinusoidal grid here, since that CRS has no EPSG code of its own. The WKT it
    writes alongside is complete and correct, but PROJ resolves the authority
    first and gives up when the lookup fails:

        PROJ: proj_create_from_database: crs not found: EPSG:996842

    rather than falling back to the body it was handed. Removing the dangling
    reference leaves a definition every client can read on its own terms. A code
    that does resolve is left alone.
    """
    from pyproj import CRS

    for name in os.listdir(directory):
        if not name.endswith(".prj"):
            continue
        path = os.path.join(directory, name)
        try:
            with open(path) as handle:
                wkt = handle.read()
        except OSError:
            continue

        match = re.search(r',\s*AUTHORITY\["([^"]+)"\s*,\s*"(\d+)"\]\s*\]\s*$',
                          wkt.strip())
        if not match:
            continue
        authority, code = match.group(1), match.group(2)
        try:
            CRS.from_user_input("%s:%s" % (authority, code))
            continue  # resolvable; leave it be
        except Exception:  # noqa: BLE001 - unresolvable is exactly the case here
            pass

        cleaned = wkt.strip()[:match.start(0)] + "]"
        try:
            CRS.from_wkt(cleaned)
        except Exception as exc:  # noqa: BLE001 - do not leave it worse
            logger.warning("Could not clean %s: %s" % (name, str(exc)[:120]))
            continue
        with open(path, "w") as handle:
            handle.write(cleaned)
        logger.info("Dropped unresolvable %s:%s from %s"
                    % (authority, code, name))


