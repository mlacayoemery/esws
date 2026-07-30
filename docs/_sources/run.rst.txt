.. _run:

=======
Running
=======

Services
========

``make up`` brings up four services. The ports below are the defaults; each is
overridable in ``.env`` (see :ref:`configuration`), so check yours if the stack is
sharing a host.

.. list-table::
   :header-rows: 1
   :widths: 18 30 52

   * - Service
     - Address
     - What it is
   * - Dashboard
     - http://localhost:8000
     - The web client: registers sources, builds jobs, tracks them
   * - WPS
     - http://localhost:5000/wps
     - Every InVEST model as a WPS 1.0 process
   * - GeoServer
     - http://localhost:8080/geoserver
     - WCS and WFS for raster and vector data
   * - File server
     - http://localhost:8001
     - Static HTTP for tables, and where table outputs are uploaded

GeoServer's default credentials are **admin** / **geoserver**.

.. code-block:: console

    make logs     # follow every service
    make down     # stop the stack and remove its volumes

The dashboard
=============

The front page lists sources by kind. Each section holds servers you have
registered, and each server lists the elements bookmarked on it.

WCS, WFS, HTTP
    Data sources. Their elements are the layers and tables a job can be given as
    input.

WPS
    Process sources. Their elements are the processes the server advertises --
    with the InVEST WPS, 26 models.

Templates
    The same processes, but their job forms arrive prefilled with InVEST's own
    sample arguments. "InVEST Demo" is registered by ``make demo``. Use it to run
    a model without hunting for inputs first.

Jobs
    Every job you have created, with its status.

Running a model
===============

1. Open a process source and pick a process. The page shows its inputs, its
   outputs, and its licence and user guide links (see :ref:`processes`).
2. Follow **New Job**. The form is generated from the process description: an
   input that wants a raster becomes a dropdown of registered WCS layers, a
   vector one of WFS layers, a table one of HTTP tables, and numbers carry the
   model's own bounds. From a Templates source it comes prefilled.
3. Submit. The job is created but not sent.
4. Follow **Run**. The job is submitted asynchronously -- the WPS answers with a
   status location rather than holding the connection open, which matters because
   some models take minutes.
5. **Status** polls it. When the run finishes, the outputs it produced are
   registered against whichever servers you chose.

.. _change-detection:

Noticing when remote data changes
=================================

A registered element points at data on someone else's server, and nothing
announces when that data is replaced. **Check for changes in remote data**, on any
WCS, WFS or HTTP source, records a fingerprint of every bookmarked element and
compares it against the last one. The element list then shows when each was last
checked and last seen to change.

Three outcomes, deliberately distinct:

changed
    The data differs from the previous check.

unchanged
    It does not. A first check is never a change: there is nothing to compare to
    yet.

unreachable
    The data could not be fetched, which is **not** the same as unchanged. Two of
    the demo's rasters land here, being the ones GeoServer will not serve
    (:ref:`crs-caveat`).

The check fetches the data. GeoServer generates OWS responses per request and
offers neither an ETag nor a Last-Modified, so there is nothing cheaper to compare;
where a source does offer a validator -- the file server does for tables -- a
matching one skips the download. Checking the demo's 39 rasters takes about 30
seconds and moves a few hundred megabytes; its 50 tables take under a second.

What counts as a change is narrower than "the bytes differ". GeoServer stamps every
entry of a shapefile archive with the *request* time, so the same untouched layer
fetched twice seconds apart has different bytes. Archives are therefore fingerprinted
by their members rather than their bytes; otherwise every check would report every
vector as changed, which is the same as reporting nothing.

Re-running when the data changes
================================

A job can ask to be re-run when the data it used is replaced. Tick **Re-run when
input data changes** on its form, and then either

* **Check inputs and re-run if changed** on the job's own page, or
* **Check inputs and re-run what changed** on the job list, which does it for every
  job that asked.

Both fingerprint the job's inputs -- matched back to registered elements from the
URLs the job holds -- and resubmit it if any of them changed *since the run that
used them*. A change from before that run is not a reason to run again.

There is no scheduler here: nothing polls on its own. The job-list action is a
single URL, so a cron entry that fetches it gives you periodic reaction:

.. code-block:: console

    */30 * * * * curl -s -o /dev/null http://localhost:8000/job/react/

Combine it with **Unique results for each run** and each reaction publishes its own
set of results rather than replacing the last.

Results
=======

Every run returns its outputs as fetchable references. Two extra inputs on each
form decide whether they are also published somewhere permanent:

Upload model results
    Publish this run's results to servers you choose -- rasters to a WCS, vectors
    to a WFS, tables to an HTTP file server. Only results are published, not the
    intermediate files a model writes while working.

    While the job runs, the outputs it is expected to produce are listed under the
    "Local Pending" sources, so you can see what is coming. On completion they
    move to the destinations you picked.

Unique results for each run
    Add a short token to the results suffix on every run, so running the same job
    again does not overwrite the previous run's outputs. Without it, a second run
    replaces the first. Once a job has finished, **Run Again** on its page
    resubmits it and says which of the two will happen.
