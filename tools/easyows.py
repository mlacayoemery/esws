import geoserver.catalog
import uuid

import urllib
import tempfile
import zipfile

ows_cache = {}

class MissingResource(Exception):
    pass

def get_cat(rest_url = "http://localhost:8080/geoserver/rest",
            username = "admin",
            password = "geoserver"):
    return geoserver.catalog.Catalog(rest_url, username, password)

def make_named_workspace(gs_cat = get_cat(),
                         prefix="user"):

    workspace_name = "-".join([prefix,
                               str(uuid.uuid1())])

    workspace_url = workspace_name

    return gs_cat.create_workspace(workspace_name, workspace_url).name
    
def publish_shp(shp_path,
                shp_name = None,
                gs_workspace = make_named_workspace(),
                gs_cat = get_cat()):

    data_store_path, _ = os.path.splitext(shp_path)
    if shp_name is None:
        shp_name = os.path.basename(data_store_path)

    shapefile_plus_sidecars = {}
    for key in ["shp", "shx", "prj", "dbf"]:
        shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

    return gs_cat.create_featurestore(shp_name,
                                      workspace = gs_workspace,
                                      data = shapefile_plus_sidecars)


def publish_tif(tif_path,
                tif_name = None,
                gs_workspace = make_named_workspace(),
                gs_cat = get_cat()):

    data_store_path, _ = os.path.splitext(tif_path)
    if tif_name is None:
        tif_name = os.path.basename(data_store_path)

    tiffdata = { 'tiff' : tif_path }

    return gs_cat.create_coveragestore_external_geotiff(tif_name,
                                                        "file://" + tif_path,
                                                        gs_cat.get_workspace(gs_workspace)) 


def extract_wrapper(args):
    extract_shapefile_value_csv(**args)

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


def local_parameters(args):
    for key, value in args.iteritems():
        if type(value) == str:
            if value[:4].lower() == "http":
                return False

    return True

def get_remote_parameters(args):
    for key, value in args.iteritems():
        if type(value) == str:
            if value[:4].lower() == "http":
                #print value
                if "service=WFS" in value:
                    if value in ows_cache:
                        args[key] = ows_cache[value]
                        print "\t\tAssigned %s cached %s" % (key, args[key])

                    else:
                        try:
                            _, tmp_path = tempfile.mkstemp(suffix=".zip", prefix="esws-")
                            urllib.URLopener().retrieve(value, tmp_path)

                            tmp_dir = tempfile.mkdtemp(prefix="esws-")
                            zipfile.ZipFile(tmp_path, 'r').extractall(tmp_dir)

                            for wfs_file in os.listdir(tmp_dir):
                                if wfs_file.endswith(".shp"):
                                    args[key] = os.path.join(tmp_dir,wfs_file)
                                    print "\t\tAssigned %s %s" % (key, args[key])
                                    ows_cache[value] = args[key]
                                    
                        except zipfile.BadZipfile:
                            print "\t\tMissing %s" % value
                            raise MissingResource, "Missing resource"

                elif "service=WCS" in value:
                    if value in ows_cache:
                        args[key] = ows_cache[value]
                        print "\t\tAssigned %s cached %s" % (key, args[key])

                    else:
                        _, tmp_path = tempfile.mkstemp(suffix=".tif", prefix="esws-")
                        urllib.URLopener().retrieve(value, tmp_path)
                        args[key] = tmp_path
                        print "\t\tAssigned %s %s" % (key, args[key])
                        ows_cache[value] = args[key]

                else:
                    raise ValueError, "Unknown protocol for %s" % value
               
def layer_url(layer_name):
    template = "http://127.0.0.1:8080/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=SHAPE-ZIP"

    return template % layer_name

def cover_url(layer_name):
    template = "http://127.0.0.1:8080/geoserver/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=%s&format=image%%2Fgeotiff"

    return template % layer_name
    
def run_job(job):
    job[0] += 1
    _, p, args, uploads, msg = job
    print "Trying %s" % msg
    if local_parameters(args):
        apply(p, [args])
        for layer_name, layer_path in uploads.iteritems():
            print "\tUploading %s" % layer_name
            ws, layer_name = layer_name.split(":")
            if layer_path.lower().endswith(".shp"):
                publish_shp(layer_path, layer_name, ws)

            elif layer_path.lower().endswith(".tif"):
                publish_tif(layer_path, layer_name, ws)

            else:
                raise ValueError, layer_path
        return True

    else:
        print "\tDownloading remote inputs"
        try:
            get_remote_parameters(job[2])

        except MissingResource:
            pass

    return False
