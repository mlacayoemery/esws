.. _tables:

============
Tabular Data
============

Tables are served over plain HTTP by the file server:

* http://localhost:8001

``make demo`` serves every table in the InVEST sample data under ``/invest/`` and
registers each as an HTTP element, selectable for any model input that wants a
table.

This stands in for the `Table Join Service
<https://www.opengeospatial.org/standards/tjs>`_: TJS describes how to publish a
table and join it to a spatial framework, but there is no maintained
implementation to serve or consume one, so tables move as files.

Tables that reference other data
================================

An InVEST table routinely names further files. A threats table lists a raster per
threat; a snapshot table a raster per year; a wave table a vector per point set.
Those names are paths relative to **the table's own directory**.

Fetching only the table therefore leaves its references dangling, and the model
stops with something like::

    Error in column "cur_path", value "/tmp/crops_c.tif": File not found

So a table fetched over HTTP has its references followed too: each is resolved
against the URL the table itself came from, downloaded with any companion files a
shapefile or raster needs, and the table is rewritten to point at the local
copies. Tables that reference tables are followed as well.

Which columns hold paths comes from the model's own specification. Habitat risk
assessment's criteria table is the exception -- a cell there holds either a number
or a raster, depending on the criterion -- so values naming a spatial file are
tried in any column. A value that is not a reference simply fails to fetch and is
left alone, so the model's own error still names what is really missing.

Uploaded results
================

Table results from a run are uploaded to the file server under ``/results/``, since
a plain file server has no upload protocol of its own. See
``WPS_TABLE_UPLOAD_DIR`` in :ref:`configuration`.
