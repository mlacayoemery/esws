import pkgutil
import natcap.invest
import inspect

import re
regex_blocks = "\n\n"
regex_param = "args\[\'"



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
    
    print title
    print abstract
    #print parameters
    
    s = re.split(regex_param,parameters)[1:]
    for p in s:
        print re.sub(" +"," ",p.replace("\n"," "))
    

