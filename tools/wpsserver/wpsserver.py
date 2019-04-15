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

pkg = "wpsprocess"
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

#http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=GetCapabilities
#http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=echo_string
#http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=echo_string&datainputs=message=Hello%20World!
#http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=echo_vector
#http://127.0.0.1:5000/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=echo_vector&datainputs=message=@xlink:href=http://127.0.0.1:8080/geoserver/cas/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=cas:watersheds&maxFeatures=50@method=GET@mimeType=text/xml@encoding=UTF-8@schema=http://schemas.opengis.net/gml/3.1.1/base/gml.xsd

#http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=vec:Count
#http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=vec:Count&datainputs=features=@xlink:http://127.0.0.1:8080/geoserver/cas/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=cas:watersheds&outputFormat=SHAPE-ZIP@method=GET@mimeType=application/zip

#http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=vec:Count&datainputs=features=@xlink:http%3A%2F%2F127.0.0.1%3A8080%2Fgeoserver%2Fcas%2Fows%3Fservice%3DWFS%26version%3D1.0.0%26request%3DGetFeature%26typeName%3Dcas%3Awatersheds%26outputFormat%3DSHAPE-ZIP@mimeType=application/zip
#http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=vec:Count&datainputs=features=%40xlink%3Ahttp%3A%2F%2F127.0.0.1%3A8080%2Fgeoserver%2Fcas%2Fows%3Fservice%3DWFS%26version%3D1.0.0%26request%3DGetFeature%26typeName%3Dcas%3Awatersheds%26outputFormat%3DSHAPE-ZIP%40method%3DGET%40mimeType%3Dapplication%2Fzip

##http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=vec:Count&datainputs=
##
##features=@xlink:
##    http://127.0.0.1:8080/geoserver/cas/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=cas:watersheds&outputFormat=SHAPE-ZIP
##@method=GET
##@mimeType=
##    application/zip
##
##features%3D%40xlink%3A
##    http%253A%252F%252F127.0.0.1%253A8080%252Fgeoserver%252Fcas%252Fows%253Fservice%253DWFS%2526version%253D1.0.0%2526request%253DGetFeature%2526typeName%253Dcas%253Awatersheds%2526outputFormat%253DSHAPE-ZIP
##%40method%3DGET
##%40mimeType%3D
##    application%252Fzip
##
##
##http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=vec:Count&datainputs=features%3D%40xlink%3Ahttp%253A%252F%252F127.0.0.1%253A8080%252Fgeoserver%252Fcas%252Fows%253Fservice%253DWFS%2526version%253D1.0.0%2526request%253DGetFeature%2526typeName%253Dcas%253Awatersheds%2526outputFormat%253DSHAPE-ZIP%40method%3DGET%40mimeType%3Dapplication%252Fzip
##
##http://127.0.0.1:8080/geoserver/wps?service=wps&version=1.0.0&request=Execute&IDENTIFIER=vec:Count&datainputs=features%3D%40xlink%3Ahttp%3A%2F%2F127.0.0.1%3A8080%2Fgeoserver%2Fcas%2Fows%3Fservice%3DWFS%26version%3D1.0.0%26request%3DGetFeature%26typeName%3Dcas%3Awatersheds%26outputFormat%3DSHAPE-ZIP%40mimeType%3Dapplication%2Fzip
##
