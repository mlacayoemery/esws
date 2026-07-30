.. _rasters:

===========
Raster Data
===========

Rasters are served by GeoServer as a `Web Coverage Service
<https://www.opengeospatial.org/standards/wcs>`_.

* Capabilities: http://localhost:8080/geoserver/ows?service=wcs&version=2.0.0&request=GetCapabilities

``make demo`` publishes every raster in the InVEST sample data into the ``invest``
workspace and registers each as a WCS element in the dashboard, where it becomes
selectable for any model input that wants a raster.

A job given a WCS URL has the coverage fetched for it before the model runs.

.. _crs-caveat:

Layers without a usable CRS
===========================

GeoServer leaves a layer **disabled** when it cannot resolve the data's native
coordinate reference system to an authority code, and then answers every request
with *Could not locate coverage* -- even though publishing reported success.

Publishing therefore identifies the CRS itself where GeoServer could not, by three
routes, in order of how much each assumes.

**The CRS can be named outright.** This covers definitions written in ESRI style
(``RGF93_Lambert_93``) and those tagged against a non-EPSG authority
(``IGNF:LAMB93``, which is plainly EPSG:2154).

**The CRS is one a vendor publishes without a code.** The MODIS sinusoidal grid is
the case that matters here: NASA prints its WKT verbatim in the LP DAAC product
guides, ``DATUM["D_unknown"]`` and all, so a file carrying it is complete rather
than damaged. It has no EPSG code and never has -- a spherical projection
referenced to WGS 84 is not something the EPSG model expresses. It is registered in
``docker/geoserver/epsg.properties`` under 996842, following the convention of the
retired SR-ORG:6842, *"MODIS Sinusoidal"*.

  Note the 99 prefix. That file extends the EPSG namespace, and **EPSG:6842 is
  already assigned**, to NAD83(2011) / Oregon Coast zone. Registering 6842 does not
  fail: GeoServer keeps its own definition and serves correct coordinates under a
  projection from the wrong side of the planet.

**Only the datum is missing.** A file can state its projection in full and name no
datum -- InVEST's Brazilian samples say UTM zone 21S on a GRS 1980 ellipsoid, then
``DATUM["D_unknown"]``. The datum is genuinely absent, not merely unlabelled: 230
datums share that ellipsoid. It makes no difference to placement, because every
modern datum on GRS 1980 or WGS 84 is geocentric and they agree to within about a
metre, so the projection is read on WGS 84. The candidate is accepted only if its
parameters match the file's exactly.

That last route is restricted to those two ellipsoids on purpose. A sphere, or an
older ellipsoid such as SAD69's International 1924, means the datum really does
differ and assuming WGS 84 would move the data tens of metres. Anything else is
refused rather than guessed, and ``make demo`` reports what it could not name.
``EASYOWS_CRS_MIN_CONFIDENCE`` lowers the bar for the first route if you accept
that trade for your own data.

One consequence for clients: a layer served under a private code carries an
``AUTHORITY`` reference no client's PROJ can resolve, and PROJ fails on the lookup
rather than falling back to the definition beside it. Data fetched for a job has
such a reference stripped, leaving a CRS every client can read on its own terms.
