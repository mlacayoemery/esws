"""Run every InVEST model through the WPS on its sample data.

Driven by the datastacks in the sample cache, so the arguments are InVEST's own
known-good ones rather than guesses. Each model is submitted as a WPS Execute
and the response is checked for ProcessSucceeded, which also implies the outputs
published to GeoServer -- a publish failure surfaces as ProcessFailed.

  python3 scripts/run_model_jobs.py                 # all models
  python3 scripts/run_model_jobs.py --only carbon sdr
  python3 scripts/run_model_jobs.py --timeout 1800

Run it inside the wps container so the sample paths resolve:

  docker compose run --rm --no-deps wps python scripts/run_model_jobs.py
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WPS_URL = os.environ.get("WPS_URL", "http://wps:5000/wps")
SAMPLES = os.environ.get("INVEST_SAMPLES_DIR", "/data/invest")

# Args the wrapper manages itself; the WPS does not accept them.
SKIP_ARGS = {"workspace_dir", "n_workers"}


GEOSERVER_BASE = os.environ.get("GEOSERVER_BASE_URL",
                                "http://geoserver:8080/geoserver")
FILESERVER = os.environ.get("FILESERVER_URL", "http://fileserver:8001")
WORKSPACE = os.environ.get("DEMO_WORKSPACE", "invest")

RASTER_EXT = (".tif", ".tiff")
VECTOR_EXT = (".shp", ".gpkg")


def ows_url(path):
    """The OWS/HTTP URL for a sample file published by scripts/load_demo.py.

    Mirrors what the generated form submits when a user picks a registered
    source from a dropdown, so this exercises the same fetch path rather than
    handing the WPS a local filename.
    """
    from load_demo import layer_name  # same naming the loader published under

    ext = os.path.splitext(path)[1].lower()
    if ext in RASTER_EXT:
        return ("%s/ows?service=WCS&version=2.0.0&request=GetCoverage"
                "&coverageId=%s:%s&format=image%%2Fgeotiff"
                % (GEOSERVER_BASE, WORKSPACE, layer_name(path)))
    if ext in VECTOR_EXT:
        return ("%s/ows?service=WFS&version=1.0.0&request=GetFeature"
                "&typeName=%s:%s&outputFormat=SHAPE-ZIP"
                % (GEOSERVER_BASE, WORKSPACE, layer_name(path)))
    if ext == ".csv":
        return "%s/invest/%s" % (FILESERVER, os.path.relpath(path, SAMPLES))
    return None


def datainput_value(value, stack_dir, use_ows=False):
    """Render one datastack arg as a WPS DataInputs value."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if not isinstance(value, str):
        return str(value)
    if not value:
        return ""
    # Datastack paths are relative to the datastack file.
    candidate = value if os.path.isabs(value) else os.path.join(stack_dir, value)
    if os.path.exists(candidate):
        resolved = os.path.realpath(candidate)
        if use_ows:
            return ows_url(resolved) or resolved
        return resolved
    return value


def build_datainputs(stack, use_ows=False):
    pairs = []
    for key, value in stack["args"].items():
        if key in SKIP_ARGS:
            continue
        rendered = datainput_value(value, stack["dir"], use_ows=use_ows)
        if rendered == "":
            continue
        pairs.append("%s=%s" % (key, rendered))
    return ";".join(pairs)


def execute(model_id, datainputs, timeout):
    params = {
        "service": "WPS",
        "version": "1.0.0",
        "request": "Execute",
        "identifier": model_id,
        "DataInputs": datainputs,
    }
    url = WPS_URL + "?" + urllib.parse.urlencode(params)
    started = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
        status = response.status
    except urllib.error.HTTPError as exc:
        return "HTTP %s" % exc.code, time.time() - started, exc.read()[:400].decode(
            "utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - timeouts and resets are results too
        return "ERROR", time.time() - started, str(exc)[:400]

    elapsed = time.time() - started
    if "ProcessSucceeded" in body:
        return "PASS", elapsed, ""
    if "ProcessFailed" in body:
        detail = ""
        start = body.find("<ows:ExceptionText>")
        if start != -1:
            detail = body[start + 19:body.find("</ows:ExceptionText>", start)]
        return "FAIL", elapsed, detail[:400]
    return "HTTP %s" % status, elapsed, body[:300]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to these model ids")
    ap.add_argument("--timeout", type=int, default=1800,
                    help="per-model timeout in seconds (default 1800)")
    ap.add_argument("--json", default=None, help="also write results here")
    ap.add_argument("--ows", action="store_true",
                    help="submit inputs as OWS/HTTP URLs to the data published "
                         "by scripts/load_demo.py, instead of local paths -- the "
                         "same references the generated form submits")
    opts = ap.parse_args()

    import invest_sample_manifest as manifest
    manifest.SAMPLES = SAMPLES
    entries, _unmatched = manifest.build()

    results = []
    for model_id in sorted(entries):
        entry = entries[model_id]
        if opts.only and model_id not in opts.only:
            continue
        if entry["excluded"]:
            results.append({"model": model_id, "status": "SKIP",
                            "seconds": 0, "detail": entry["excluded"]})
            print("%-36s SKIP   %s" % (model_id, entry["excluded"]), flush=True)
            continue
        if not entry["datastacks"]:
            results.append({"model": model_id, "status": "NODATA",
                            "seconds": 0, "detail": "no datastack in the samples"})
            print("%-36s NODATA no sample args" % model_id, flush=True)
            continue

        stack = entry["datastacks"][0]
        datainputs = build_datainputs(stack, use_ows=opts.ows)
        status, elapsed, detail = execute(model_id, datainputs, opts.timeout)
        results.append({"model": model_id, "status": status,
                        "seconds": round(elapsed, 1), "detail": detail})
        line = "%-36s %-6s %6.1fs" % (model_id, status, elapsed)
        if detail:
            line += "  " + " ".join(detail.split())[:110]
        print(line, flush=True)

    passed = sum(1 for r in results if r["status"] == "PASS")
    print("\n%d passed, %d failed, %d skipped, %d without data (of %d)" % (
        passed,
        sum(1 for r in results if r["status"] not in ("PASS", "SKIP", "NODATA")),
        sum(1 for r in results if r["status"] == "SKIP"),
        sum(1 for r in results if r["status"] == "NODATA"),
        len(results)))

    if opts.json:
        with open(opts.json, "w") as fh:
            json.dump(results, fh, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
