.. _vectors:

===========
Vector Data
===========

Vectors are served by GeoServer as a `Web Feature Service
<https://www.opengeospatial.org/standards/wfs>`_.

* Capabilities: http://localhost:8080/geoserver/ows?service=wfs&version=1.0.0&request=GetCapabilities

``make demo`` publishes every vector in the InVEST sample data into the ``invest``
workspace and registers each as a WFS element, selectable for any model input that
wants a vector.

A job given a WFS URL has the features fetched as a zipped shapefile and unpacked
before the model runs. The same CRS caveat applies as for rasters
(:ref:`crs-caveat`).
