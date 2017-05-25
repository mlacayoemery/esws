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
