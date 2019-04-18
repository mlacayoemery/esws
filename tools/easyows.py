import logging
import os

import geoserver.catalog
import uuid

import urllib

try:
    #Python2
    import urllib
    urlretrieve = urllib.URLopener().retrieve
    
except ImportError:
    #Python
    from urllib.request import urlretrieve

import re

import tempfile
import zipfile

class MissingResource(Exception):
    pass

class Catalog:
    def __init__(self,
                 gs_url = "http://localhost:8080/geoserver",
                 username = "admin",
                 password = "geoserver",
                 ws_prefix = "user-",
                 logger = logging.getLogger('easyows')):

        self.gs_url = gs_url
        self.username = username
        self.password = password
        self.gs_cat = self.get_cat(self.gs_url + "/rest")
        self.ws_prefix = ws_prefix

        self.logger = logger

        self.ows_cache = {}

    def get_cat(self, rest_url):
        "Creates connection to catalog"
        
        return geoserver.catalog.Catalog(rest_url,
                                         username = self.username,
                                         password = self.password)

    def make_named_workspace(self):
        "Creates workspace with UUID and returns name"

        workspace_name = self.ws_prefix + str(uuid.uuid1())

        try:
            return self.gs_cat.create_workspace(workspace_name).name

        except TypeError:
            #gsconfig 2.0.1
            return self.gs_cat.create_workspace(workspace_name, workspace_name).name

    def clean_named_workspace(self,
                              f = None):

        if f is None:
            def f(s):
                return s[:5] == self.ws_prefix

        for ws in self.gs_cat.get_workspaces():
            if f(ws.name):
                self.logger.info("%s" % ws.name)
                self.gs_cat.delete(ws, recurse=True)
        
    
    def publish_shp(self,
                    shp_path,
                    shp_name = None,
                    gs_workspace = None):
        "Publishes a Shapefile to a workspace"

        if gs_workspace is None:
            gs_workspace = self.make_named_workspace()

        data_store_path, _ = os.path.splitext(shp_path)
        if shp_name is None:
            shp_name = os.path.basename(data_store_path)

        shapefile_plus_sidecars = {}
        for key in ["shp", "shx", "prj", "dbf"]:
            shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

        return self.gs_cat.create_featurestore(shp_name,
                                               workspace = gs_workspace,
                                               data = shapefile_plus_sidecars)


    def publish_tif(self,
                    tif_path,
                    tif_name = None,
                    gs_workspace = None):
        "Publishes a GeoTIFF to a workspace"

        if gs_workspace is None:
            gs_workspace = self.make_named_workspace()

        data_store_path, _ = os.path.splitext(tif_path)
        if tif_name is None:
            tif_name = os.path.basename(data_store_path)

        tiffdata = { 'tiff' : tif_path }

        return self.gs_cat.create_coveragestore(name = tif_name,
                                                path = "file://" + tif_path,
                                                workspace = self.gs_cat.get_workspace(gs_workspace),
                                                layer_name = tif_name) 

    def layer_url(self,layer_name):
        template = self.gs_url + "/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=SHAPE-ZIP"

        return template % layer_name

    def layer_name_from_url(self,layer_url):
        return re.search("typeName=(.+)&", layer_url).group(1)

    def cover_url(self,layer_name):
        template = self.gs_url + "/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=%s&format=image%%2Fgeotiff"

        return template % layer_name

    def cover_name_from_url(self, cover_url):
        return re.search("coverageId=(.+)&", cover_url).group(1)

    def store_exists(self, name, workspace):
        return len(self.gs_cat.get_stores(names=name, workspaces=workspace)) > 0


class Job:
    def __init__(self,
                 process,
                 args,
                 uploads,
                 msg,
                 priority=0,                 
                 catalog = Catalog(),                 
                 logger = logging.getLogger('easyows')):

        self.catalog = catalog
        self.priority = priority
        self.process = process
        self.args = args
        self.uploads = uploads
        self.msg = msg
        self.logger = logger

    def are_local_parameters(self):
        "Boolean of whether all the arguments to the process are local"
        for key, value in self.args.iteritems():
            if type(value) == str:
                if value[:4].lower() == "http":
                    return False

        return True

    def get_remote_parameters(self,
                              ows_cache = None,
                              prefix = "esws-"):
        "Get any remote parameters with option cache"

        if ows_cache is None:
            self.logger.debug("Trying catalog cache %i" % id(self.catalog.ows_cache))
            ows_cache=self.catalog.ows_cache
        else:
            self.logger.debug("Checking given OWS cache")
        
        for key, value in self.args.iteritems():
            if type(value) == str:
                if value[:4].lower() == "http":
                    self.logger.debug("Found remote parameter %s" % value)
                    #print value
                    if "service=WFS" in value:
                        self.logger.debug("Detected WFS service")
                        if value in ows_cache:
                            self.args[key] = ows_cache[value]
                            self.logger.info("Assigned %s cached %s" % (key, self.args[key]))

                        else:
                            workspace, name = self.catalog.layer_name_from_url(value).split(":")
                            self.logger.debug("Checking for %s in %s" % (name,workspace))
                            if self.catalog.store_exists(name, workspace):
                                self.logger.debug("Remote resource exists")
                            else:
                                self.logger.debug("Remote resource does not exist")
                                raise MissingResource("Missing resource")
                            
                            try:
                                _, tmp_path = tempfile.mkstemp(suffix=".zip", prefix=prefix)
                                urllib.URLopener().retrieve(value, tmp_path)

                                tmp_dir = tempfile.mkdtemp(prefix=prefix)
                                zipfile.ZipFile(tmp_path, 'r').extractall(tmp_dir)

                                for wfs_file in os.listdir(tmp_dir):
                                    if wfs_file.endswith(".shp"):
                                        self.args[key] = os.path.join(tmp_dir,wfs_file)
                                        self.logger.info("Assigned %s %s" % (key, self.args[key]))
                                        ows_cache[value] = self.args[key]
                                        
                            except zipfile.BadZipfile:
                                self.logger.error("Missing %s" % value)
                                raise MissingResource("Missing resource")

                    elif "service=WCS" in value:
                        self.logger.debug("Detected WCS service")
                        if value in ows_cache:
                            self.args[key] = ows_cache[value]
                            self.logger.info("Assigned %s cached %s" % (key, self.args[key]))

                        else:
                            workspace, name = self.catalog.cover_name_from_url(value).split(":")
                            self.logger.debug("Checking for %s in %s" % (name,workspace))                            
                            if self.catalog.store_exists(name, workspace):
                                self.logger.debug("Remote resource exists")
                            else:
                                self.logger.debug("Remote resource does not exist")
                                raise MissingResource("Missing resource")
                            
                            _, tmp_path = tempfile.mkstemp(suffix=".tif", prefix=prefix)
                            urllib.URLopener().retrieve(value, tmp_path)
                            self.args[key] = tmp_path
                            self.logger.info("Assigned %s %s" % (key, self.args[key]))
                            ows_cache[value] = self.args[key]

                    else:
                        self.logger.error("Unknown protocol for %s" % value)
                        raise ValueError("Unknown protocol for %s" % value)
    
    def run(self, increment=1):
        self.logger.info("Trying %s" % self.msg)
        
        self.priority += increment
        self.logger.debug("Job priority %i" % self.priority)        

        if self.are_local_parameters():
            apply(self.process, [self.args])
            
            for layer_name, layer_path in self.uploads.iteritems():
                self.logger.info("Uploading %s" % layer_name)
                ws, layer_name = layer_name.split(":")
                if layer_path.lower().endswith(".shp"):
                    self.catalog.publish_shp(layer_path, layer_name, ws)

                elif layer_path.lower().endswith(".tif"):
                    self.catalog.publish_tif(layer_path, layer_name, ws)

                else:
                    self.logger.error("Unknown file type %s" % layer_path)
                    raise ValueError(layer_path)
            return True

        else:
            self.logger.info("Downloading remote parameters")
            try:
                self.get_remote_parameters()

            except MissingResource:
                self.logger.debug("Could not download all remote parameters")

            except IOError:
                self.logger.debug("Could not download all remote parameters")


        return False
