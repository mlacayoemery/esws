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

@app.route('/wps', methods=['GET', 'POST'])
def wps():
    return service

bind_host='0.0.0.0'
app.run(threaded=True,host=bind_host)
