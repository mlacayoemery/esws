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

Publishing therefore identifies the CRS itself where GeoServer could not, and
declares it, which covers definitions written in ESRI style (``RGF93_Lambert_93``)
or tagged against a non-EPSG authority (``IGNF:LAMB93``, which is EPSG:2154).

A match below 90% confidence is refused rather than guessed: declaring the wrong
CRS silently puts the data in the wrong place, which is worse than a layer that
plainly does not work. Two rasters in the InVEST samples carry an unnamed
projection whose best candidates are three different UTM zone 21S datums at 70%
apiece; they stay unpublished and ``make demo`` names them. Lower the bar with
``EASYOWS_CRS_MIN_CONFIDENCE`` if you accept that trade for your own data.
