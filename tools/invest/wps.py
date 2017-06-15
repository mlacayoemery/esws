import pkgutil
import natcap.invest
import inspect
import os
import pkg_resources

import re
regex_blocks = "([A-Za-z ]+)[.\n]+(.*)Parameters:(.*)Returns"
regex_param = "args\[\'([a-z\_]+)\'\] \(([a-z]+)\): ([a-z \n]+)"

import logging
logging_format = '%(asctime)s %(name)-20s %(levelname)-8s %(message)s'
#logging_format = '%(levelname)-8s %(message)s'
logging.basicConfig(format=logging_format,
                    level=logging.DEBUG,
                    datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('esws.tools.invest')

LOGGER.setLevel(logging.INFO)
LOGGER.setLevel(logging.DEBUG)

def parse_tool():
    exclude = ["natcap.invest.iui"]
    include = ["natcap.invest.sdr"]#,
    ##           "natcap.invest.carbon"]

    package = natcap.invest
    prefix = package.__name__ + "."

    version = natcap.invest.__version__
    if version == "3.3.3":
        LOGGER.info("%s version of InVEST found." % version)
    else:
        LOGGER.warn("%s version found insted of version 3.3.3.")
        
    modules = []
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
        LOGGER.debug("%s submodule found." % modname)
        if modname in include:
            modules.append(modname)
            LOGGER.info("%s added to module list." % modname)

    wps_processes = []
    for modname in modules:
        LOGGER.info("%s module processing." % modname)
        module = __import__(modname, fromlist="dummy")
        LOGGER.debug("%s imported." % modname)

        doc = inspect.getdoc(module.execute)
    #    l = re.split(regex_blocks, doc)
        title, abstract, parameters = re.search(regex_blocks, doc, re.DOTALL).groups()

        abstract = re.sub(' +',' ',re.sub("\n", " ", abstract))
        
        LOGGER.info("%s model name found." % title)
        LOGGER.debug("\"%s\" model abstract found." % abstract)

        #pywps.inout.literaltypes.LITERAL_DATA_TYPES
        #pywps.inout.formats.FORMATS
        for p, t, d in re.findall(regex_param, parameters):
            #remove newlines and repeated spaces from description
            d = re.sub(' +',' ',re.sub("\n", " ", d))
            LOGGER.debug("%s model parameter found." % p)        
            if t == "number":
                LOGGER.debug("%s model parameter type found." % t)          
            elif t == "string":
                if "dir" in p:
                    LOGGER.debug("%s model parameter type found." % "dir")
                elif "suffix" in p:
                    LOGGER.debug("%s model parameter type found." % "string")
                elif "watershed" in p:
                    LOGGER.debug("%s model parameter type found." % "vector")             
                elif "table" in p or "table" in d:
                    LOGGER.debug("%s model parameter type found." % "table")               
                elif "raster" or "lulc" in d:
                    LOGGER.debug("%s model parameter type found." % "raster")              
                else:
                    LOGGER.debug("%s model string parameter type found." % "UNKNOWN")
                    raise TypeError, "%s is an unknown string type" % p
            elif t == "bool":
                LOGGER.debug("%s model parameter type found." % "bool")              
            else:
                raise TypeError, "%s is an unknown parameter type" % t

            LOGGER.debug("\"%s\" model parameter description found." % d)
            
            #print re.sub(" +"," ",p.replace("\n"," "))

        outputs_dict = natcap.invest.sdr._OUTPUT_BASE_FILES
        for k in outputs_dict.keys():
            ext = os.path.splitext(outputs_dict[k])[-1]
            print k,
            if ext == ".tif":
                print "raster"
            elif ext == ".shp":
                print "shapefile"
            elif ext == ".csv":
                print "csv"
            else:
                print "ERROR"

        print
        outputs_dict = natcap.invest.sdr._INTERMEDIATE_BASE_FILES
        for k in outputs_dict.keys():
            ext = os.path.splitext(outputs_dict[k])[-1]
            print k,
            if ext == ".tif":
                print "raster"
            elif ext == ".shp":
                print "shapefile"
            elif ext == ".csv":
                print "csv"
            else:
                print "ERROR"

        print        
        outputs_dict = natcap.invest.sdr._TMP_BASE_FILES
        for k in outputs_dict.keys():
            ext = os.path.splitext(outputs_dict[k])[-1]
            print k,
            if ext == ".tif":
                print "raster"
            elif ext == ".shp":
                print "shapefile"
            elif ext == ".csv":
                print "csv"
            else:
                print "ERROR"

    resource_package = "natcap.invest" # Could be any module/package name
    resource_path = '/'.join(('iui', 'sdr.json'))  # Do not use os.path.join(), see below

    template = pkg_resources.resource_string(resource_package, resource_path)
    # or for a file-like stream:
    #template = pkg_resources.resource_stream(resource_package, resource_path)
    return wps_processes

import os
import flask

import pywps

class SayHello(pywps.Process):
    def __init__(self):
        inputs = [pywps.LiteralInput('name', 'Input name', data_type='string')]
        outputs = [pywps.LiteralOutput('response',
                                 'Output response', data_type='string')]

        super(SayHello, self).__init__(
            self._handler,
            identifier='say_hello',
            title='Process Say Hello',
            abstract='Returns a literal string output\
             with Hello plus the inputed name',
            version='1.3.3.7',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        response.outputs['response'].data = 'Hello ' + \
            request.inputs['name'][0].data
        response.outputs['response'].uom = pywps.UOM('unity')
        return response



def handler(request, response):
    response.outputs['response'].data = 'Hello ' + \
        request.inputs['name'][0].data
    response.outputs['response'].uom = pywps.UOM('unity')
    return response

def ProcessClassInstance(name = "SayHello",
                         inputs = [pywps.LiteralInput('name', 'Input name', data_type='string')],
                         outputs = [pywps.LiteralOutput('response', 'Output response', data_type='string')],
                         handler = handler,
                         identifier='say_hello',
                         title='Process Say Hello',
                         abstract='Returns a literal string output with Hello plus the inputed name',
                         version='1.3.3.7',
                         store_supported=True,
                         status_supported=True):
    def __init__(self):
        self.inputs = inputs
        self.outputs = outputs

        self._handler = handler
    
        pywps.Process.__init__(self,
            self._handler,
            identifier=identifier,
            title=title,
            abstract=abstract,
            version=version,
            inputs=self.inputs,
            outputs=self.outputs,
            store_supported=store_supported,
            status_supported=store_supported)
    
    process_class = type(name, (pywps.Process,),{"__init__": __init__})
    return process_class()

wps_process = []
wps_process.append(ProcessClassInstance())


def handler(request, response):
    response.outputs['response'].data = 'Goodbye ' + \
        request.inputs['name'][0].data
    response.outputs['response'].uom = pywps.UOM('unity')
    return response
wps_process.append(ProcessClassInstance(name = "SayGoodbye",
                                        handler=handler,
                                        identifier='say_goodbye',
                                        title="Process Say Goodbye",
                                        abstract="What you would expect"))


def handler(request, response):
    response.outputs['response'].data = request.inputs['interjection'][0].data + " " + request.inputs['noun'][0].data
    response.outputs['response'].uom = pywps.UOM('unity')
    return response

wps_process.append(ProcessClassInstance(name = "InterjectionNoun",
                                        inputs = [pywps.LiteralInput('interjection', 'Input interjection', data_type='string'),
                                                  pywps.LiteralInput('noun', 'Input noun', data_type='string')],
                                        outputs = [pywps.LiteralOutput('response', 'Output response', data_type='string')],                                                                                
                                        handler=handler,
                                        identifier='interjection_noun',
                                        title="Process Interjection Noun",
                                        abstract="What you would expect"))

def handler(request, response):
    out = "/home/mlacayo/Downloads/outlets.gml"
    response.outputs['gml_out'].output_format = pywps.FORMATS.GML
    response.outputs['gml_out'].file = out
    return response

wps_process.append(ProcessClassInstance(name = "send_gml",
                                        inputs = [],
                                        outputs = [pywps.ComplexOutput('gml_out',
                                                                       'GML file',
                                                                       supported_formats=[pywps.Format('application/gml+xml')])],
                                        handler = handler,
                                        identifier='send_gml',
                                        title='Process to send a GML file',
                                        abstract='Returns a GML file'))
                                       

#http://localhost:5000/wps?request=Execute&service=WPS&identifier=send_shp&version=1.0.0&ResponseDocument=shp_out=@asReference=true
def handler(request, response):
    out = "/home/mlacayo/Downloads/watersheds.zip"
    response.outputs['shp_out'].output_format = pywps.FORMATS.SHP
    response.outputs['shp_out'].file = out
    return response

wps_process.append(ProcessClassInstance(name = "send_shp",
                                        inputs = [],
                                        outputs = [pywps.ComplexOutput('shp_out',
                                                                       'SHP file',
                                                                       supported_formats=[pywps.Format('application/x-zipped-shp')])],
                                        handler = handler,
                                        identifier='send_shp',
                                        title='Process to send a SHP file',
                                        abstract='Returns a SHP file'))

#http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=echo_shp&version=1.0.0
#http://localhost:5000/wps?request=Execute&service=WPS&identifier=echo_shp&version=1.0.0&ResponseDocument=shp_out=@asReference=true&datainputs=shp_in=http://gala.unige.ch:8080/geoserver/wfs?typename=geonode%3Awatersheds&outputFormat=SHAPE-ZIP&version=1.0.0&service=WFS&request=GetFeature
#http://localhost:5000/wps?request=Execute&service=WPS&identifier=echo_shp&version=1.0.0&datainputs=shp_in=Reference@xlink:href=
def handler(request, response):
    out = request.inputs['shp_in'][0].data
    response.outputs['shp_out'].output_format = pywps.FORMATS.SHP
    response.outputs['shp_out'].file = out
    return response

wps_process.append(ProcessClassInstance(name = "EchoSHP",
                                        inputs = [pywps.ComplexInput('shp_in',
                                                                      'SHP in',
                                                                      supported_formats=[pywps.Format('application/x-zipped-shp')])],
                                        outputs = [pywps.ComplexOutput('shp_out',
                                                                       'SHP out',
                                                                       supported_formats=[pywps.Format('application/x-zipped-shp')])],
                                        handler = handler,
                                        identifier='echo_shp',
                                        title='Process to echo a SHP file',
                                        abstract='Returns a the given SHP file'))


##def handler(request, response):
##    response.outputs['response'].data = 'Goodbye ' + \
##        request.inputs['name'][0].data
##    response.outputs['response'].uom = pywps.UOM('unity')
##    return response
##wps_process.append(ProcessClassInstance(name = "echowfs",
##                                        inputs = [pywps.ComplexInput('inputwfs',
##                                                                     'inputwfs',
##                                                                     supported_formats = ["WFS"],
##                                                                     data_format = "WFS",
##                                                                     abstract="A WFS call",
##                                                                     min_occurs=1,
##                                                                     max_occurs=1],
##                                        outputs = [pywps.ComplexOutput('outputwfs',
##                                                                       'outputwfs',
##                                                                       supported_formats = ["WFS"],
##                                                                       abstract="A WFS call")],
##                                        handler=handler,
##                                        identifier='echowfs',
##                                        title="Process to get a wfs resource",
##                                        abstract="What you would expect"))


app = flask.Flask(__name__)

#http://localhost:5000/wps?request=GetCapabilities&service=WPS
#http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
#http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=say_hello&version=1.0.0
#http://localhost:5000/wps?request=Execute&datainputs=name=World!&service=WPS&identifier=say_hello&version=1.0.0
#http://localhost:5000/wps?request=Execute&datainputs=name=World!&service=WPS&identifier=say_goodbye&version=1.0.0
#http://localhost:5000/wps?service=WPS&version=1.0.0&request=GetExecutionStatus&executionId=0b9ef4c4-51b2-11e7-af67-80e650054182
#http://localhost:5000/wps?request=Execute&service=WPS&identifier=send_gml&version=1.0.0


#http://localhost:5000/wps?request=Execute&datainputs=interjection=Hello;noun=World!&service=WPS&identifier=interjection_noun&version=1.0.0

#http://apps.esdi-humboldt.cz/pywps/?service=WPS&version=1.0.0&request=Execute&identifier=literalprocess&datainputs=[int=1;float=3.2;zeroset=0;string=spam]&storeExecuteResponse=false


processes = []
processes.extend(wps_process)

# For the process list on the home page

process_descriptor = {}
for process in processes:
    abstract = process.abstract
    identifier = process.identifier
    process_descriptor[identifier] = abstract

# This is, how you start PyWPS instance
service = pywps.Service(processes, ['pywps.cfg'])


@app.route("/")
def hello():
    server_url = pywps.configuration.get_config_value("server", "url")
    request_url = flask.request.url
    return flask.render_template('home.htm', request_url=request_url,
                                 server_url=server_url,
                                 process_descriptor=process_descriptor)


@app.route('/wps', methods=['GET', 'POST'])
def wps():

    return service


@app.route('/outputs/'+'<filename>')
def outputfile(filename):
    targetfile = os.path.join('outputs', filename)
    if os.path.isfile(targetfile):
        file_ext = os.path.splitext(targetfile)[1]
        with open(targetfile, mode='rb') as f:
            file_bytes = f.read()
        mime_type = None
        if 'xml' in file_ext:
            mime_type = 'text/xml'
        return flask.Response(file_bytes, content_type=mime_type)
    else:
        flask.abort(404)


@app.route('/static/'+'<filename>')
def staticfile(filename):
    targetfile = os.path.join('static', filename)
    if os.path.isfile(targetfile):
        with open(targetfile, mode='rb') as f:
            file_bytes = f.read()
        mime_type = None
        return flask.Response(file_bytes, content_type=mime_type)
    else:
        flask.abort(404)

if __name__ == "__mainmain__":
    parse_tool()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="""Script for starting PyWPS
         demo instance with sample processes""",
        epilog="""Do not use demo in production environment.
         It's intended to be running in test environment only!
        For more documentation, visit http://pywps.org/doc
        """
        )
    parser.add_argument('-d', '--daemon',
                        action='store_true', help="run in daemon mode")
    parser.add_argument('-a','--all-addresses',
                        action='store_true', help="run flask using IPv4 0.0.0.0 (all network interfaces),"  +  
                            "otherwise bind to 127.0.0.1 (localhost).  This maybe necessary in systems that only run Flask") 
    args = parser.parse_args()
    
    if args.all_addresses:
        bind_host='0.0.0.0'
    else:
        bind_host='127.0.0.1'

    if args.daemon:
        pid = None
        try:
            pid = os.fork()
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        if (pid == 0):
            os.setsid()
            app.run(threaded=True,host=bind_host)
        else:
            os._exit(0)
    else:
        app.run(threaded=True,host=bind_host)
