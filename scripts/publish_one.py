"""Run one model through the WPS with uploads on, so publishing is exercised.

run_model_jobs.py deliberately leaves upload_results alone -- it checks that
models *run*. This asks for the results to be published as well, which is what
the layout and backend settings decide, and is otherwise only reachable by
driving the dashboard's job form.

  docker compose run --rm --no-deps wps python scripts/publish_one.py [model]
"""
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WPS = os.environ.get("WPS_URL", "http://wps:5000/wps")
GEOSERVER = os.environ.get("GEOSERVER_BASE_URL", "http://geoserver:8080/geoserver")
FILESERVER = os.environ.get("FILESERVER_URL", "http://fileserver:8001")
SAMPLES = os.environ.get("INVEST_SAMPLES_DIR", "/data/invest")


def main():
    model_id = sys.argv[1] if len(sys.argv) > 1 else "annual_water_yield"

    import invest_sample_manifest as manifest
    import run_model_jobs as runner
    manifest.SAMPLES = SAMPLES
    runner.SAMPLES = SAMPLES
    entries, _unmatched = manifest.build()

    entry = entries.get(model_id)
    if not entry or not entry["datastacks"]:
        print("no sample arguments for %s" % model_id)
        return 1

    datainputs = runner.build_datainputs(entry["datastacks"][0], use_ows=True)
    # The wrapper's own inputs: publish, and where to.
    for key, value in (("upload_results", "true"),
                       ("destination_wcs", GEOSERVER),
                       ("destination_wfs", GEOSERVER),
                       ("destination_http", FILESERVER)):
        datainputs += ";%s=%s" % (key, urllib.parse.quote(value, safe=""))

    url = "%s?%s" % (WPS, urllib.parse.urlencode({
        "service": "WPS", "version": "1.0.0", "request": "Execute",
        "identifier": model_id, "DataInputs": datainputs}))
    with urllib.request.urlopen(url, timeout=1800) as response:
        body = response.read().decode("utf-8", "replace")

    ok = "ProcessSucceeded" in body
    print("%s -> %s" % (model_id, "PUBLISHED" if ok else "FAILED"))
    if not ok:
        print(body[:1200])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
