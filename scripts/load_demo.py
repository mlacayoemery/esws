"""Load the ESWS demo: publish InVEST sample data and register it in the dashboard.

Runs inside the wps container (it needs natcap.invest, easyows and the sample
data mount). Driven by the datastacks in the sample cache, so it publishes the
files the models actually take as input rather than everything on disk.

  rasters (.tif)         -> GeoServer coverage  -> registered as WCS elements
  vectors (.shp/.gpkg)   -> GeoServer datastore -> registered as WFS elements
  tables  (.csv)         -> served by fileserver -> registered as CSV elements

Everything lands in one stable GeoServer workspace (default ``invest``) so layer
names are predictable, unlike the per-job uuid workspaces the WPS creates.

Idempotent: existing layers and registrations are left alone, so re-running
tops up rather than duplicating.

  make demo
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, "/app/tools")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

import easyows  # noqa: E402

WORKSPACE = os.environ.get("DEMO_WORKSPACE", "invest")
DASHBOARD = os.environ.get("DASHBOARD_URL", "http://dashboard:8000")
FILESERVER = os.environ.get("FILESERVER_URL", "http://fileserver:8001")
WPS = os.environ.get("WPS_URL", "http://wps:5000/wps")
# The dashboard's get_ows_data_url appends "/ows?..." itself, so this is the
# GeoServer base -- adding /ows here would produce .../ows/ows?...
GEOSERVER_BASE = os.environ.get("GEOSERVER_BASE_URL",
                                "http://geoserver:8080/geoserver")
SAMPLES = os.environ.get("INVEST_SAMPLES_DIR", "/data/invest")

RASTER_EXT = (".tif", ".tiff")
VECTOR_EXT = (".shp", ".gpkg")
TABLE_EXT = (".csv",)


def log(msg):
    print(msg, flush=True)


def http_get(url, timeout=120):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


# --------------------------------------------------------------------------- #
# what to publish
# --------------------------------------------------------------------------- #
def referenced_files():
    """{abs_path: kind} for every file the sample datastacks pass as an arg."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import invest_sample_manifest as manifest

    manifest.SAMPLES = SAMPLES
    entries, _unmatched = manifest.build()

    found = {}
    for entry in entries.values():
        if entry["excluded"]:
            continue
        for stack in entry["datastacks"]:
            for value in stack["args"].values():
                if not isinstance(value, str) or not value:
                    continue
                path = value if os.path.isabs(value) else os.path.join(stack["dir"], value)
                if not os.path.exists(path):
                    continue
                ext = os.path.splitext(path)[1].lower()
                if ext in RASTER_EXT:
                    found[os.path.realpath(path)] = "raster"
                elif ext in VECTOR_EXT:
                    found[os.path.realpath(path)] = "vector"
                elif ext in TABLE_EXT:
                    found[os.path.realpath(path)] = "table"
    return found


def layer_name(path):
    """A GeoServer-safe, collision-resistant layer name for a sample file.

    Qualified by the sample set (the top directory under the cache root) rather
    than the immediate parent: basenames repeat across models, and so does the
    parent, since most sets keep their data in an `input/` subdirectory --
    WaveEnergy and ScenicQuality both ship `input/AOI_WCVI.shp`.
    """
    base = os.path.splitext(os.path.basename(path))[0]
    try:
        dataset = os.path.relpath(path, SAMPLES).split(os.sep)[0]
    except ValueError:
        dataset = ""
    name = "%s_%s" % (dataset, base) if dataset and dataset != base else base
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name).strip("_").lower()


# --------------------------------------------------------------------------- #
# publishing
# --------------------------------------------------------------------------- #
def ensure_workspace(cat):
    existing = {w.name for w in cat.gs_cat.get_workspaces()}
    if WORKSPACE not in existing:
        cat.gs_cat.create_workspace(WORKSPACE, "http://esws/%s" % WORKSPACE)
        log("   created workspace %s" % WORKSPACE)
    return WORKSPACE


def publish(cat, files):
    """Publish rasters and vectors; return {kind: [layer_name]}."""
    published = {"raster": [], "vector": [], "table": []}
    existing = {l.name.split(":")[-1] for l in cat.gs_cat.get_layers()}

    for path, kind in sorted(files.items()):
        if kind == "table":
            published["table"].append(path)
            continue

        name = layer_name(path)
        if name in existing:
            published[kind].append(name)
            continue

        try:
            if kind == "raster":
                cat.publish_tif(path, tif_name=name, gs_workspace=WORKSPACE)
            elif path.lower().endswith(".gpkg"):
                cat.publish_gpkg(path, gpkg_name=name, gs_workspace=WORKSPACE)
            else:
                cat.publish_shp(path, shp_name=name, gs_workspace=WORKSPACE)
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the load
            log("   ! %-44s %s" % (name, str(exc)[:90]))
            continue
        published[kind].append(name)
        log("   + %-8s %s" % (kind, name))

    return published


# --------------------------------------------------------------------------- #
# dashboard registration
# --------------------------------------------------------------------------- #
def register_server(server_type, title, url):
    """Register a source and return its primary key (existing one if present)."""
    path = "/server/%s/register/%s/url/%s" % (
        server_type, urllib.parse.quote(title), url)
    status, _ = http_get(DASHBOARD + path)
    if status != 200:
        raise RuntimeError("register %s -> HTTP %s" % (server_type, status))

    status, body = http_get("%s/server/%s/" % (DASHBOARD, server_type))
    import re
    pks = [int(p) for p in re.findall(r"/server/%s/(\d+)/" % server_type, body)]
    if not pks:
        raise RuntimeError("no %s server registered" % server_type)
    return max(pks)


def register_elements(server_type, server_pk, element_ids):
    ok = 0
    for element_id in element_ids:
        path = "/server/%s/%d/register/%s/" % (server_type, server_pk,
                                               urllib.parse.quote(element_id))
        try:
            status, _ = http_get(DASHBOARD + path)
            ok += status == 200
        except Exception as exc:  # noqa: BLE001
            log("   ! element %s: %s" % (element_id, str(exc)[:80]))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-publish", action="store_true",
                    help="register sources only; do not touch GeoServer")
    opts = ap.parse_args()

    log(">> Collecting sample data referenced by the InVEST datastacks")
    files = referenced_files()
    counts = {k: sum(1 for v in files.values() if v == k)
              for k in ("raster", "vector", "table")}
    log("   %(raster)d rasters, %(vector)d vectors, %(table)d tables" % counts)

    published = {"raster": [], "vector": [], "table": []}
    if not opts.skip_publish:
        log(">> Publishing to GeoServer")
        cat = easyows.Catalog.from_env()
        ensure_workspace(cat)
        published = publish(cat, files)
    else:
        published["table"] = [p for p, k in files.items() if k == "table"]

    log(">> Registering sources in the dashboard")
    csv_pk = register_server("CSV", "Local HTTP", FILESERVER)
    wcs_pk = register_server("WCS", "Local WCS", GEOSERVER_BASE)
    wfs_pk = register_server("WFS", "Local WFS", GEOSERVER_BASE)
    wps_pk = register_server("WPS", "InVEST WPS", WPS)
    # Same WPS, listed under Templates: its job forms come prefilled with the
    # sample arguments from the datastacks.
    tpl_pk = register_server("TPL", "InVEST Demo", WPS)
    log("   CSV=%d WCS=%d WFS=%d WPS=%d TPL=%d"
        % (csv_pk, wcs_pk, wfs_pk, wps_pk, tpl_pk))

    log(">> Registering elements")
    n_wcs = register_elements("WCS", wcs_pk,
                              ["%s:%s" % (WORKSPACE, n) for n in published["raster"]])
    n_wfs = register_elements("WFS", wfs_pk,
                              ["%s:%s" % (WORKSPACE, n) for n in published["vector"]])
    tables = [os.path.relpath(p, SAMPLES) for p in published["table"]]
    n_csv = register_elements("CSV", csv_pk, ["invest/%s" % t for t in tables])
    log("   %d WCS, %d WFS, %d CSV elements" % (n_wcs, n_wfs, n_csv))

    log(">> Demo loaded. Dashboard: %s/server/WPS/%d/element/" % (DASHBOARD, wps_pk))


if __name__ == "__main__":
    main()
