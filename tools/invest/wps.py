import pkgutil
import natcap.invest
import inspect

import re
regex_blocks = "\n\n"
regex_param = "args\[\'([a-z\_]+)\'\] \(([a-z]+)\): ([a-z ]+)"



import logging
logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('esws.tools.invest')

LOGGER.setLevel(logging.INFO)
LOGGER.setLevel(logging.DEBUG)

exclude = ["natcap.invest.iui"]
include = ["natcap.invest.sdr"]

package = natcap.invest
prefix = package.__name__ + "."

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
    l = re.split(regex_blocks, doc)
    title, abstract, parameters = l[:3]

    title = title.strip(".")
    abstract = abstract.replace("\n"," ").replace("  ", " ")
    
    LOGGER.info("%s model name found." % title)
    LOGGER.debug("\"%s\" model abstract found." % abstract)
    
    for p, t, d in re.findall(regex_param, parameters):
        LOGGER.debug("%s model parameter found." % p)        
        if t == "number":
            LOGGER.debug("%s model parameter type found." % t)          
        elif t == "string":
            if "dir" in p:
                LOGGER.debug("%s model parameter type found." % "dir")
            elif "watershed" in p:
                LOGGER.debug("%s model parameter type found." % "vector")             
            elif "table" in p:
                LOGGER.debug("%s model parameter type found." % "table")               
            elif "raster" or "lulc" in d:
                LOGGER.debug("%s model parameter type found." % "raster")              
            else:
                LOGGER.debug("%s model string parameter type found." % "UNKNOWN")
                raise TypeError, "%s is an unknown string type" % p

        else:
            raise TypeError, "%s is an unknown parameter type" % t

        LOGGER.debug("\"%s\" model parameter description found." % d)
        
        #print re.sub(" +"," ",p.replace("\n"," "))
