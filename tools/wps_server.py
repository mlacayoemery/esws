import logging
import os
import importlib
import flask
import pywps

logging.basicConfig(filename='esws.log',
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

logging.getLogger().addHandler(logging.StreamHandler())

logging.info("WPS server starting.")

pkg = "test"
process_path = os.path.join(os.path.dirname(__file__), pkg)

app = flask.Flask(__name__)

wps_processes = []

for file_name in os.listdir(process_path):
    if file_name != "__init__.py" and file_name.endswith(".py"):
        module_name = os.path.splitext(file_name)[0]
        m = importlib.import_module(".".join([pkg,
                                              module_name]))
        logging.debug("Found process %s" % module_name)
        c = getattr(m, "WebProcess")
        
        wps_processes.append(c())

service = pywps.Service(wps_processes)

@app.route('/wps', methods=['GET', 'POST'])
def wps():
    return service

bind_host='127.0.0.1'
app.run(threaded=True,host=bind_host)
