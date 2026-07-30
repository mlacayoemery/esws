.. _processes:

=========
Processes
=========

The WPS exposes every InVEST model as a `Web Processing Service
<https://www.opengeospatial.org/standards/wps>`_ 1.0 process -- 26 of them, built
from InVEST's own model registry rather than written by hand.

* Capabilities: http://localhost:5000/wps?service=WPS&version=1.0.0&request=GetCapabilities

:ref:`models` has the inputs of each model as a diagram.

What a process description carries
==================================

Inputs
------

Each model argument becomes a process input, typed as the model types it. WPS has
no way to say "this input wants a raster", so the InVEST type travels in the
input's abstract as a machine-readable trailer::

    [invest:type=raster invest:required=do_valuation]

which is what lets the dashboard offer registered WCS layers for it instead of a
text box. ``invest:required`` appears when an input is conditional: whether it
applies depends on the values of other inputs.

Bounds and units
----------------

A numeric input publishes the model's own constraint, so a value the model would
reject can be caught before a job is submitted. 80 of the 101 numeric inputs have
one.

Two-sided bounds are ``ows:AllowedValues`` with an ``ows:Range``, whose closure
distinguishes strict from non-strict: a ratio is 0 to 1 inclusive, while a
seasonality constant must be *greater* than 0. One-sided bounds travel in the
abstract trailer instead (``invest:min``, ``invest:max``, ``invest:exclusive``),
because a range with no upper bound cannot be expressed there.

Units are ``ows:UOM``: "24 meter" and "24 hectare" are not the same input.

Outputs
-------

Every file a model produces is declared as its own output and returned as a URL
rather than inline. What a *given* run will produce is worked out before it starts,
conditional outputs included, which is what lets the dashboard list a job's
outputs while it is still queued.

Licence and documentation
-------------------------

A process runs an InVEST model through this wrapper, so two licences apply and
neither could otherwise be inferred from the service. Both are declared as
``ows:Metadata`` with the OGC licence role, alongside the model's own manual:

* MIT -- the ESWS WPS wrapper
* Apache-2.0 -- the InVEST model implementation
* the InVEST user guide page for that model

The dashboard shows all three on the process page.

Extra inputs
============

Four inputs on every process are the wrapper's own rather than the model's. They
decide where results go; see :ref:`run`.

``upload_results``
    Publish this run's results to the servers named below.

``destination_wcs``, ``destination_wfs``, ``destination_http``
    Where rasters, vectors and tables go respectively. The dashboard fills these
    in from the servers you have registered.

Asynchronous execution
======================

Runs are submitted with ``storeExecuteResponse``, so the server answers
immediately with a status location and the client polls it. Some models take
minutes -- scenic quality is around four -- and a synchronous request would hold
the connection open for the whole run.

InVEST Average Annual Water Yield
=================================

.. invest-inputs:: annual_water_yield
