import logging
import os
import importlib
import flask
import pywps
import sys

logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

logging.info("WPS server starting.")

pkg = "wpsprocess"
process_path = os.path.join(os.path.dirname(__file__), pkg)

app = flask.Flask(__name__)

wps_processes = []

for file_name in os.listdir(process_path):
    if file_name != "__init__.py" and file_name.endswith(".py"):
        module_name = os.path.splitext(file_name)[0]
        logging.debug("Found process module %s" % module_name)

        try:
            m = importlib.import_module(".".join([pkg, module_name]))
        except Exception as exc:
            logging.exception("Could not import process module %s: %s",
                              module_name, exc)
            continue

        # A module may expose either a get_processes() factory returning a list
        # (e.g. invest_models.py, one process per InVEST model) or a single
        # WebProcess class (the legacy convention).
        if hasattr(m, "get_processes"):
            try:
                wps_processes.extend(m.get_processes())
            except Exception as exc:
                logging.exception("get_processes() failed in %s: %s",
                                  module_name, exc)
        elif hasattr(m, "WebProcess"):
            wps_processes.append(m.WebProcess())
        else:
            logging.debug("Module %s exposes no WPS process", module_name)

logging.info("Registered %d WPS processes", len(wps_processes))

config_file=os.path.join(os.path.dirname(__file__), "pywps.cfg")
service = pywps.Service(wps_processes, config_file)

# The URL clients are handed for stored documents and referenced outputs. It has
# to match how they reach this server, not the port inside the container -- same
# reasoning as GEOSERVER_PUBLIC_URL in docker-compose.yml.
_output_url = os.environ.get("WPS_OUTPUT_URL")
if _output_url:
    pywps.configuration.CONFIG.set("server", "outputurl", _output_url)

_output_path = pywps.configuration.get_config_value("server", "outputpath")

@app.route('/wps', methods=['GET', 'POST'])
def wps():
    return service

@app.route('/outputs/<path:filename>')
def outputs(filename):
    """Serve what pywps stored under outputpath.

    Asynchronous execution (storeExecuteResponse=true) answers immediately with
    a statusLocation pointing here, and asReference=true returns outputs as URLs
    under the same path. Without this route both are written to disk and then
    404 to the client, so the whole asynchronous flow is unusable.
    """
    return flask.send_from_directory(_output_path, filename)

bind_host='0.0.0.0'
app.run(threaded=True,host=bind_host)
