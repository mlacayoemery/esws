.. _install:

============
Installation
============

ESWS runs as four containers: the WPS server, the dashboard, a GeoServer, and a
static file server. Docker Compose is the supported way to run it.

Docker Compose
==============

Requirements
------------

* Docker Engine with the Compose plugin (``docker compose``, not
  ``docker-compose``)
* Around 8 GB of disk for the images, and another 2 GB if you load the InVEST
  sample data

Quick start
-----------

.. code-block:: console

    git clone https://github.com/mlacayoemery/esws.git
    cd esws
    cp .env.example .env      # optional: adjust ports and credentials
    make build
    make up

The build takes a while: the WPS image installs GDAL and InVEST from conda-forge.
``make up`` on its own builds only images that do not exist yet, so run
``make build`` after anything that changes what gets installed.

See :ref:`run` for the addresses the services come up on, and
:ref:`configuration` for what ``.env`` controls.

Loading the sample data
-----------------------

The stack starts empty on purpose: nothing is registered and no data is
published. One command fills it in.

.. code-block:: console

    make demo

That downloads the InVEST sample datasets (about 2 GB, cached outside the
repository under ``/store/invest`` by default), publishes every raster and vector
they contain to GeoServer, serves the tables over HTTP, and registers all of it in
the dashboard along with a WPS source and a Templates source.

The download is the slow part and is skipped once cached, so ``make demo`` is
cheap to repeat. It is idempotent: layers already published are left in place,
though they are re-checked, which repairs any that an earlier load left disabled
(see :ref:`crs-caveat`).

Tests
-----

.. code-block:: console

    make unit         # seconds: needs neither the stack nor InVEST. What CI runs.
    make smoke        # builds, starts the stack, runs the suite, tears down
    make smoke-demo   # the same with the demo loaded, so no test skips

Bare metal
==========

``install.sh`` installs ESWS directly onto Ubuntu, without containers. It is kept
working, but it is the harder path: it needs a system GDAL matching the InVEST
build, a Java runtime for GeoServer, and root.

.. code-block:: console

    sudo ./install.sh

Two targets check that path still works, each in a throwaway container:

.. code-block:: console

    make check-baremetal   # install.sh + the requirements install on a clean machine
    make check-geoserver   # the GeoServer step produces a GeoServer that serves

Legacy virtual machine
======================

Before containers, ESWS was distributed as a VirtualBox appliance running every
service in one Ubuntu guest, at fixed addresses on a host-only network
(192.168.56.104), with an older InVEST and GeoServer 2.15 under ``/gs215``.

That appliance is no longer available for download, and nothing else in this
documentation describes it. Use Compose.
