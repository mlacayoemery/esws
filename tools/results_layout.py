"""Where a run's results go on the destination server.

Every job should produce a unique, traceable result, and none of them should be
thrown away. Two layouts satisfy that, and they differ in how a result is
*addressed* rather than merely where it is stored:

``run``
    A workspace per run, named for the run. Layer names stay exactly as the model
    wrote them -- ``run_a1b2c3d4:wyield``, not ``results:wyield_gura_a1b2c3d4``.
    Uniqueness is structural, so nothing has to be mangled into a name, and
    dropping a run is one delete. Each run is also its own OGC endpoint, since
    GeoServer serves every workspace at ``/geoserver/<workspace>/ows``.

    The cost is catalog growth: GeoServer keeps its catalog as XML on disk, at
    roughly four files per layer, so this scales with the number of runs.

``series``
    One layer per model output, and a granule per run, addressed by time.
    ``series:sdr_sed_export&time=2026-07-31T09:00:00Z``. The catalog stops
    growing with run count, which is what makes "keep everything" survivable in
    the long run, and asking for a layer without a time gets the most recent --
    so a downstream job following "whatever A last produced" needs no
    resolution logic at all.

    The cost is that appending to a series needs a store that supports it. A
    shapefile does not, so vectors in this layout require the PostGIS backend.

The vector backend is chosen separately, since it is useful on its own:

``files``
    Shapefiles, as GeoServer has always taken them.

``postgis``
    Tables in PostGIS. No sidecar files, no 2 GB or 10-character-column limits,
    real indexes, and the data is reachable by SQL -- which is the substrate a
    table join service would want.

Kept free of GeoServer and GDAL so the naming rules can be exercised on their own.
"""
import os
import re

LAYOUT_RUN = "run"
LAYOUT_SERIES = "series"
BACKEND_FILES = "files"
BACKEND_POSTGIS = "postgis"

# Workspace holding the series layers. Runs get a workspace each, named below.
SERIES_WORKSPACE = os.environ.get("ESWS_SERIES_WORKSPACE", "series")
RUN_WORKSPACE_PREFIX = os.environ.get("ESWS_RUN_WORKSPACE_PREFIX", "run_")

# Column carrying the run time on a PostGIS series table, and the granule
# attribute GeoServer exposes as the layer's time dimension.
TIME_COLUMN = "esws_run_time"


def layout(value=None):
    """The configured layout, defaulting to a workspace per run."""
    chosen = (value if value is not None
              else os.environ.get("ESWS_RESULTS_LAYOUT", LAYOUT_RUN)).strip().lower()
    return chosen if chosen in (LAYOUT_RUN, LAYOUT_SERIES) else LAYOUT_RUN


def vector_backend(value=None):
    """The configured vector backend, defaulting to shapefiles."""
    chosen = (value if value is not None
              else os.environ.get("ESWS_VECTOR_BACKEND",
                                  BACKEND_FILES)).strip().lower()
    return chosen if chosen in (BACKEND_FILES, BACKEND_POSTGIS) else BACKEND_FILES


def safe(name):
    """A GeoServer-safe name.

    Workspace names become XML namespace prefixes and layer names travel in URLs,
    so both are restricted to NCName characters, and neither may begin with a
    digit.
    """
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", str(name)).strip("_")
    if not cleaned:
        return "unnamed"
    return cleaned if not cleaned[0].isdigit() else "n" + cleaned


def run_workspace(run_id):
    """The workspace a single run publishes into, under the ``run`` layout."""
    return safe(RUN_WORKSPACE_PREFIX + str(run_id))


def series_layer(model_id, output_name):
    """The layer an output accumulates into, under the ``series`` layout.

    Named for the model and the output rather than the file, so every run of the
    same model lands in the same series no matter what results_suffix was set --
    that suffix is the user's label, and two runs labelled differently are still
    the same output.
    """
    return safe("%s_%s" % (model_id, output_name))


def target(kind, model_id, output_name, run_id, chosen_layout=None):
    """(workspace, layer) for one output.

    ``output_name`` is the name the model gave the file, suffix and all; under
    ``run`` it is kept verbatim, since the workspace already makes it unique.
    """
    if layout(chosen_layout) == LAYOUT_SERIES:
        return SERIES_WORKSPACE, series_layer(model_id, output_name)
    return run_workspace(run_id), safe(output_name)


def unsuffixed(output_name, results_suffix):
    """``output_name`` with the run's results_suffix removed.

    A series has to recognise the same output across runs, and results_suffix is
    the one part of the name that legitimately differs between them.
    """
    if not results_suffix:
        return output_name
    suffix = str(results_suffix)
    if not suffix.startswith("_"):
        suffix = "_" + suffix
    return (output_name[:-len(suffix)]
            if output_name.endswith(suffix) else output_name)


def requires_postgis(kind, chosen_layout=None, backend=None):
    """Whether this combination cannot be served by the file backend.

    A series of vectors is appended to run after run, and a shapefile cannot be
    appended to. Rasters are fine either way: a mosaic is a directory of files.
    """
    return (kind == "vector"
            and layout(chosen_layout) == LAYOUT_SERIES
            and vector_backend(backend) != BACKEND_POSTGIS)
