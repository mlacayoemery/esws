.. _index:

Ecosystem Service Web Service
=============================

Ecosystem Service Web Service (ESWS) is a method for creating
interoperable analysis workflows with the Open Geospatial Consortium
(OGC)
`Web Services (OWS) standards
<https://www.opengeospatial.org/standards/common>`_
, especially the
`Table Join Service (TJS)
<https://www.opengeospatial.org/standards/tjs>`_,
`Web Coverage Service (WCS)
<https://www.opengeospatial.org/standards/wcs>`_,
`Web Feature Service (WFS)
<https://www.opengeospatial.org/standards/wfs>`_, and
`Web Processing Service (WPS)
<https://www.opengeospatial.org/standards/wps>`_.

ESWS workflows are:

* modular
* redistributable
* open

ESWS runs as four containers -- a WPS server exposing every
`InVEST <https://naturalcapitalproject.stanford.edu/software/invest>`_ model, a
GeoServer, a file server, and a dashboard that ties them together. Pick data from
whichever server holds it, run a model on it, and have the results published back
to a server of your choosing.

Resources:
----------
* `GitHub Repository <https://github.com/mlacayoemery/esws>`_


Contents:
---------

.. toctree::
   :maxdepth: 4

   install
   run
   configuration
   tables
   rasters
   vectors
   processes
   models
   extensions
   tut

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
