import logging
import os

import geoserver.catalog
import uuid

import urllib

import sys
if sys.version_info.major == 2:
    import urllib
    urlretrieve = urllib.URLopener().retrieve
    unquote = urllib.unquote

else:
    from urllib.request import urlretrieve
    from urllib.parse import unquote

import re

import tempfile
import zipfile

#import ogr

class MissingResource(Exception):
    pass


class _GeoServer3Catalog(geoserver.catalog.Catalog):
    """geoserver-restconfig with the trailing slashes GeoServer 3 rejects.

    The client (2.0.16, the latest release) builds some REST paths with a
    trailing slash -- ``create_workspace`` posts to ``/rest/namespaces/``.
    GeoServer 2.x tolerated that; 3.0 routes strictly and answers::

        404 {"detail":"No endpoint POST /geoserver/rest/namespaces/."}

    while the identical request to ``/rest/namespaces`` returns 201. Normalising
    the path here fixes every call site at once rather than only the workspace
    creation that happens to fail first. Harmless against GeoServer 2.x, which
    accepts the path either way.
    """

    def http_request(self, url, data=None, method='get', headers=None):
        head, sep, query = url.partition('?')
        if head.endswith('/'):
            url = head.rstrip('/') + sep + query
        return super().http_request(url, data=data, method=method,
                                    headers=headers or {})

class Catalog:
    def __init__(self,
                 gs_url = "http://localhost:8080/geoserver",
                 username = "admin",
                 password = "geoserver",
                 ws_prefix = "user-",
                 logger = logging.getLogger('easyows')):

        self.logger = logger
        self.gs_url = gs_url
        self.username = username
        self.password = password
        self.gs_cat = self.get_cat(self.gs_url + "/rest")
        self.ws_prefix = ws_prefix

        self.ows_cache = {}

    @classmethod
    def from_env(cls, logger=logging.getLogger('easyows')):
        "Builds a Catalog from GEOSERVER_* environment variables (container config)"
        return cls(
            gs_url=os.environ.get("GEOSERVER_URL", "http://localhost:8080/geoserver"),
            username=os.environ.get("GEOSERVER_USER", "admin"),
            password=os.environ.get("GEOSERVER_PASS", "geoserver"),
            ws_prefix=os.environ.get("WPS_WORKSPACE_PREFIX", "esws-"),
            logger=logger,
        )

    def get_cat(self, rest_url):
        "Creates connection to catalog"
        self.logger.debug("Connecting to catalog %s" % rest_url)
        
        return _GeoServer3Catalog(rest_url,
                                  username = self.username,
                                  password = self.password)

    def make_named_workspace(self, ws_uuid=None):
        "Creates workspace with UUID and returns name"

        if ws_uuid is None:
            workspace_name = self.ws_prefix + str(uuid.uuid1())
        else:
            workspace_name = self.ws_prefix + ws_uuid

        self.logger.debug("Attempting to create workspace %s" % workspace_name)

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

        self.logger.debug("Cleaning workspace")

        for ws in self.gs_cat.get_workspaces():
            if f(ws.name):
                self.logger.debug("%s" % ws.name)
                self.gs_cat.delete(ws, recurse=True)
        
    
    def publish_shp(self,
                    shp_path,
                    shp_name = None,
                    gs_workspace = None,
                    overwrite = False):
        """Publishes a Shapefile to a workspace

        overwrite replaces a store of the same name; without it GeoServer
        rejects the request outright ("There is already a store named ..."), so
        publishing the same layer twice -- a model re-run, a reloaded demo --
        silently produces nothing.
        """

        if gs_workspace is None:
            gs_workspace = self.make_named_workspace()

        data_store_path, _ = os.path.splitext(shp_path)
        if shp_name is None:
            shp_name = os.path.basename(data_store_path)

        shapefile_plus_sidecars = {}
        for key in ["shp", "shx", "prj", "dbf"]:
            shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

##        driver = ogr.GetDriverByName("ESRI Shapefile")
##        data = driver.Open(shp_path, 1)
##        layer = data.GetLayer()
##        for feature in layer:
##            feature.GetGeomRef().GetEnvelope()

        return self.gs_cat.create_featurestore(shp_name,
                                               workspace = gs_workspace,
                                               data = shapefile_plus_sidecars,
                                               overwrite = overwrite)


    def publish_tif(self,
                    tif_path,
                    tif_name = None,
                    gs_workspace = None,
                    overwrite = False):
        "Publishes a GeoTIFF to a workspace. See publish_shp for overwrite."

        if gs_workspace is None:
            gs_workspace = self.make_named_workspace()

        data_store_path, _ = os.path.splitext(tif_path)
        if tif_name is None:
            tif_name = os.path.basename(data_store_path)

        tiffdata = { 'tiff' : tif_path }

        # upload_data=True uploads the GeoTIFF to GeoServer over REST, so the
        # (separate) GeoServer container does not need filesystem access to the
        # WPS workspace.
        return self.gs_cat.create_coveragestore(name = tif_name,
                                                path = tif_path,
                                                workspace = self.gs_cat.get_workspace(gs_workspace),
                                                layer_name = tif_name,
                                                upload_data = True,
                                                overwrite = overwrite)

    def publish_gpkg(self,
                     gpkg_path,
                     gpkg_name = None,
                     gs_workspace = None,
                     overwrite = False):
        "Publishes a GeoPackage by translating it to a Shapefile with GDAL first"

        from osgeo import gdal

        if gpkg_name is None:
            gpkg_name = os.path.splitext(os.path.basename(gpkg_path))[0]

        tmp_dir = tempfile.mkdtemp(prefix="esws-gpkg-")
        shp_path = os.path.join(tmp_dir, gpkg_name + ".shp")

        self.logger.debug("Translating %s to %s" % (gpkg_path, shp_path))
        gdal.VectorTranslate(shp_path, gpkg_path, format="ESRI Shapefile")

        return self.publish_shp(shp_path, gpkg_name, gs_workspace, overwrite)

    def layer_url(self,layer_name):
        template = self.gs_url + "/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=SHAPE-ZIP"

        return template % layer_name

    def layer_name_from_url(self,layer_url):
        if not layer_url[:4].lower() == "http":
            raise ValueError("Not a vaild URL")

        if layer_url[4] == "%":
            self.logger.debug("Found quoted URL")
            return re.search("typeName=(.+)&", unquote(layer_url)).group(1)
        else:
            return re.search("typeName=(.+)&", layer_url).group(1)

    def cover_url(self,layer_name):
        template = self.gs_url + "/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=%s&format=image%%2Fgeotiff"

        return template % layer_name

    def cover_name_from_url(self, cover_url):
        if not cover_url[:4].lower() == "http":
            raise ValueError("Not a vaild URL")

        if cover_url[4] == "%":
            self.logger.debug("Found quoted URL")
            return re.search("coverageId=(.+)&", unquote(cover_url)).group(1)
        else:
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

        self.logger = logger

        logger.debug("Construting job with args %s" % str(args))
        
        self.catalog = catalog
        self.priority = priority
        self.process = process
        self.args = args
        self.uploads = uploads
        self.msg = msg
        # {layer_name: reason} for outputs the model produced but GeoServer
        # would not accept; reported rather than raised, see run().
        self.failed_uploads = {}


    def are_local_parameters(self):
        "Boolean of whether all the arguments to the process are local"

        for key, value in self.args.items():
            if isinstance(value, str):
                self.logger.debug("Checking locality of %s" % value)

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

        failure = False
        failure_list = []
        for key, value in self.args.items():
            try:
                if isinstance(value, str):
                    if value[:4].lower() == "http":
                        self.logger.debug("Found remote parameter %s" % value)
                        if value[4] == "%":
                            self.logger.debug("Found quoted URL")
                            value = unquote(value)
                        #print value
                        if "service=WFS" in value:
                            self.logger.debug("Detected WFS service")
                            if value in ows_cache:
                                self.args[key] = ows_cache[value]
                                self.logger.debug("Assigned %s cached %s" % (key, self.args[key]))

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
                                    urlretrieve(value, tmp_path)

                                    tmp_dir = tempfile.mkdtemp(prefix=prefix)
                                    zipfile.ZipFile(tmp_path, 'r').extractall(tmp_dir)

                                    for wfs_file in os.listdir(tmp_dir):
                                        if wfs_file.endswith(".shp"):
                                            self.args[key] = os.path.join(tmp_dir,wfs_file)
                                            self.logger.debug("Assigned %s %s" % (key, self.args[key]))
                                            ows_cache[value] = self.args[key]
                                            
                                except zipfile.BadZipfile:
                                    self.logger.error("Missing %s" % value)
                                    raise MissingResource("Missing resource")

                        elif "service=WCS" in value:
                            self.logger.debug("Detected WCS service")
                            if value in ows_cache:
                                self.args[key] = ows_cache[value]
                                self.logger.debug("Assigned %s cached %s" % (key, self.args[key]))

                            else:
                                workspace, name = self.catalog.cover_name_from_url(value).split(":")
                                self.logger.debug("Checking for %s in %s" % (name,workspace))                            
                                if self.catalog.store_exists(name, workspace):
                                    self.logger.debug("Remote resource exists")
                                else:
                                    self.logger.debug("Remote resource does not exist")
                                    raise MissingResource("Missing resource")
                                
                                _, tmp_path = tempfile.mkstemp(suffix=".tif", prefix=prefix)
                                urlretrieve(value, tmp_path)
                                self.args[key] = tmp_path
                                self.logger.debug("Assigned %s %s" % (key, self.args[key]))
                                ows_cache[value] = self.args[key]

                        else:
                            #self.logger.error("Unknown protocol for %s" % value)
                            #raise ValueError("Unknown protocol for %s" % value)

                            self.logger.debug("Trying simple HTTP get")
                            if value in ows_cache:
                                self.args[key] = ows_cache[value]
                                self.logger.debug("Assigned %s cached %s" % (key, self.args[key]))

                            else:                               
                                _, tmp_path = tempfile.mkstemp(suffix=".csv", prefix=prefix)
                                urlretrieve(value, tmp_path)
                                self.args[key] = tmp_path
                                self.logger.debug("Assigned %s %s" % (key, self.args[key]))
                                ows_cache[value] = self.args[key]                            
                            
            except MissingResource:
                self.logger.debug("Continuing after missing resource detected")
                failure = True
                failure_list.append("%s:%s" % (workspace, name))
                
        if failure:
            self.logger.debug("Missing resources(s) %s" % str(failure_list))
            raise MissingResource("Missing resource")
        
    def run(self, increment=1):
        self.logger.debug("Trying %s" % self.msg)
        
        self.priority += increment
        self.logger.debug("Job priority %i" % self.priority)        

        if self.are_local_parameters():
            self.logger.debug("Local parameters detected")
            self.process(self.args)

            for layer_name, layer_path in self.uploads.items():
                if not os.path.exists(layer_path):
                    self.logger.warning("Skipping missing output %s" % layer_path)
                    continue
                self.logger.debug("Uploading %s" % layer_name)
                ws, layer_name = layer_name.split(":")
                try:
                    if layer_path.lower().endswith(".shp"):
                        self.catalog.publish_shp(layer_path, layer_name, ws)

                    elif layer_path.lower().endswith(".tif"):
                        self.catalog.publish_tif(layer_path, layer_name, ws)

                    elif layer_path.lower().endswith(".gpkg"):
                        self.catalog.publish_gpkg(layer_path, layer_name, ws)

                    else:
                        self.logger.warning("Skipping unsupported output type %s"
                                            % layer_path)
                except Exception as exc:  # noqa: BLE001
                    # One unpublishable output must not fail a model run that
                    # otherwise succeeded. Several models emit convolution
                    # kernels (search_kernel, area_kernel, gaussian_kernel) as
                    # intermediate rasters; they carry no CRS, so GeoServer
                    # answers 500 when asked to make a coverage of them.
                    self.failed_uploads[layer_name] = str(exc)
                    self.logger.warning("Could not publish %s: %s",
                                        layer_name, str(exc)[:200])
            return True

        else:
            self.logger.debug("Downloading remote parameters")
            try:
                self.get_remote_parameters()

            except MissingResource:
                self.logger.debug("Could not download all remote parameters")

            except IOError:
                self.logger.debug("Could not download all remote parameters")


        return False
