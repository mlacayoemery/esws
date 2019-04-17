import logging

import geoserver.catalog
import uuid

import urllib
import tempfile
import zipfile

class MissingResource(Exception):
    pass

class Catalog:
    def __init__(self,
                 gs_url = "http://localhost:8080/geoserver",
                 username = "admin",
                 password = "geoserver",
                 ws_prefix = "user-"):

        self.gs_url = gs_url
        self.username = username
        self.password = password
        self.gs_cat = self.get_cat(self.gs_url + "/rest")
        self.ws_prefix = ws_prefix

        self.ows_cache = {}

    def get_cat(self, rest_url):
        "Creates connection to catalog"
        
        return geoserver.catalog.Catalog(rest_url,
                                         username = self.username,
                                         password = self.password)

    def make_named_workspace(self):
        "Creates workspace with UUID and returns name"
        
        return gs_cat.create_workspace(self.ws_prefix + str(uuid.uuid1())).name
    
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

        return gs_cat.create_coveragestore_external_geotiff(tif_name,
                                                            "file://" + tif_path,
                                                            self.gs_cat.get_workspace(gs_workspace)) 

    def layer_url(self,layer_name):
        template = self.gs_url + "/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=SHAPE-ZIP"

        return template % layer_name

    def cover_url(self,layer_name):
        template = self.gs_url + "/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=%s&format=image%%2Fgeotiff"

        return template % layer_name


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
            ows_cache=self.catalog.ows_cache
        
        for key, value in self.args.iteritems():
            if type(value) == str:
                if value[:4].lower() == "http":
                    #print value
                    if "service=WFS" in value:
                        if value in ows_cache:
                            self.args[key] = ows_cache[value]
                            self.logger.info("Assigned %s cached %s" % (key, self.args[key]))

                        else:
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
                        if value in ows_cache:
                            self.args[key] = ows_cache[value]
                            self.logger.info("Assigned %s cached %s" % (key, self.args[key]))

                        else:
                            _, tmp_path = tempfile.mkstemp(suffix=".tif", prefix=prefix)
                            urllib.URLopener().retrieve(value, tmp_path)
                            self.args[key] = tmp_path
                            self.logger.info("Assigned %s %s" % (key, self.args[key]))
                            ows_cache[value] = self.args[key]

                    else:
                        self.logger.error("Unknown protocol for %s" % value)
                        raise ValueError("Unknown protocol for %s" % value)
    
    def run(self, increment=1):
        self.priority += increment

        self.logger.info("Trying %s" % self.msg)
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
            self.logger.info("Downloading remote inputs")
            try:
                self.get_remote_parameters()

            except MissingResource:
                pass

        return False

def extract_wrapper(args):
    self.extract_shapefile_value_csv(**args)

def extract_shapefile_value_csv(shapefile_path, key, csv_path, id_field="ws_id", id_value=1, value_field="sed_retent"):
    #open the output results
    data_source = driver.Open(shapefile_path, 0)

    #get the actual data from the results
    layer = data_source.GetLayer()

    #loop over each feature in the data
    for feature in layer:

        #check if watershed 1 found
        if feature.GetField(id_field) == 1:

            #save retention
            with open(csv_path, 'ab') as csvfile:
                datawriter = csv.writer(csvfile)
                datawriter.writerow([key, feature.GetField(value_field)])

            data_source = None

            return None
