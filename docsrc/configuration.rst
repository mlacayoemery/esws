.. _configuration:

===========================
Configuration & Maintenance
===========================

Everything here is optional: the defaults work.

Environment
===========

``docker-compose.yml`` reads ``.env``. Copy ``.env.example`` and edit it.

Host ports
----------

Container ports never change; these decide what the host publishes them on. Set
them when the defaults collide with something else.

.. list-table::
   :header-rows: 1
   :widths: 32 12 56

   * - Variable
     - Default
     - Service
   * - ``DASHBOARD_HOST_PORT``
     - 8000
     - Dashboard
   * - ``WPS_HOST_PORT``
     - 5000
     - WPS
   * - ``FILESERVER_HOST_PORT``
     - 8001
     - File server
   * - ``GEOSERVER_HOST_PORT``
     - 8080
     - GeoServer

``GEOSERVER_HOST_PORT`` and ``WPS_HOST_PORT`` do double duty: they also determine
the addresses those services advertise to clients, since a URL handed out to a
browser has to be reachable from the host rather than from inside the network.

Credentials
-----------

``GEOSERVER_USER`` and ``GEOSERVER_PASS`` (**admin** / **geoserver**) are used both
by GeoServer itself and by the WPS when it publishes results.

Data and results
----------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Variable
     - Meaning
   * - ``INVEST_SAMPLES``
     - Where the InVEST sample data is cached. Defaults to
       ``/store/invest/samples``; kept outside the repository because it is
       around 2 GB. Mounted read-only.
   * - ``WPS_RESULTS_WORKSPACE``
     - GeoServer workspace uploaded results are published into (``results``).
   * - ``WPS_TABLE_UPLOAD_DIR``
     - Directory table results are copied into. It is a volume the file server
       publishes, which is what makes an HTTP destination a real upload target: a
       plain file server has no upload protocol of its own. Leave it unset and
       tables are reported where the WPS already serves them from.
   * - ``WPS_TABLE_UPLOAD_PATH``
     - The path that directory appears at on the file server (``results``).
   * - ``EASYOWS_CRS_MIN_CONFIDENCE``
     - How sure a CRS match must be, as a percentage, before it is declared for a
       published layer. Defaults to 90. See :ref:`crs-caveat`.
   * - ``INVEST_USERGUIDE_BASE``
     - Base URL each process links its manual under.

Maintenance
===========

Updating
--------

.. code-block:: console

    git pull
    make build   # only needed if the pull changed what gets installed
    make up

A pull that touches the InVEST or GDAL pins means a WPS image rebuild, which takes
several minutes.

State
-----

The stack keeps its state in Docker volumes: GeoServer's catalogue, the published
raster and vector data, uploaded table results, and the WPS output store. The
dashboard's database lives inside its container, so recreating that container
starts it empty -- run ``make demo`` again to repopulate.

``make down`` removes all of it. There is no separate reset.
