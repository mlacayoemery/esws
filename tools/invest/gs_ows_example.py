if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import easyows

import copy

import natcap.invest.scenario_gen_proximity
import natcap.invest.sdr

import osgeo.ogr
import os

import geoserver.catalog
import uuid

import csv

import urllib
import tempfile
import zipfile

class MissingResource(Exception):
    pass

def get_cat(rest_url = "http://localhost:8080/gs213/rest",
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

ows_cache = {}

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
   
data_path = "/home/mlacayo/workspace/cas/data"

#http://127.0.0.1:8080/geoserver/cas/wms?service=WMS&version=1.1.0&request=GetMap&layers=cas:eto&styles=&bbox=444900.9029974863,4900407.170489954,485070.9029974863,4956627.170489954&width=548&height=768&srs=EPSG:26910&format=image%2Fgeotiff
#http://127.0.0.1:8080/geoserver/cas/wcs?service=WCS&version=1.0.0&request=GetCoverage&coverage=cas:eto&bbox=444900.9029974863,4900407.170489954,485070.9029974863,4956627.170489954&width=548&height=768&crs=EPSG:26910&format=image%2Fgeotiff
#http://127.0.0.1:8080/geoserver/ows?service=WCS&version=1.0.0&request=DescribeCoverage&coverage=cas:eto

#http://127.0.0.1:8080/geoserver/cas/wcs?service=WCS&version=2.0.0&request=GetCoverage&coverageId=cas:eto&&format=image%2Fgeotiff

sdr_base_args = {
    u'biophysical_table_path': u'/home/mlacayo/workspace/cas/data/biophysical_table.csv',
    u'dem_path': cover_url("cas:dem"),
    u'drainage_path': u'',
    u'erodibility_path': cover_url("cas:erodibility"),
    u'erosivity_path': cover_url("cas:erosivity"),
    u'ic_0_param': u'0.5',
    u'k_param': u'2',
    u'lulc_path': cover_url("cas:landuse_90"),
    u'sdr_max': u'0.8',
    u'threshold_flow_accumulation': u'1000',
    u'watersheds_path': layer_url("cas:watersheds"),
    u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/sdr_base',
    }

#convert 50,000 HA (~36%) of pasture (type 80) to conifers (type 56)
#when it is near any age conifers (types 56, 57, 58, 59, 60, 61)
gen_forest_args = {
    u'aoi_path': u'',
    u'area_to_convert': u'50000',
    u'base_lulc_path': cover_url("cas:landuse_90"),
    u'convert_farthest_from_edge': False,
    u'convert_nearest_to_edge': True,
    u'convertible_landcover_codes': u'80',
    u'focal_landcover_codes': u'56 57 58 59 60 61',
    u'n_fragmentation_steps': u'1',
    u'replacment_lucode': u'56',
    u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/scenario_forest',
    }

#convert 50,000 HA (~36%) of pasture (type 80) to low density residential (type 1)
#when it is near any density residential (types 1, 2, 3 4)
gen_residential_args = {
    u'aoi_path': u'',
    u'area_to_convert': u'50000',
    u'base_lulc_path': cover_url("cas:landuse_90"),
    u'convert_farthest_from_edge': False,
    u'convert_nearest_to_edge': True,
    u'convertible_landcover_codes': u'80',
    u'focal_landcover_codes': u'1 2 3 4',
    u'n_fragmentation_steps': u'1',
    u'replacment_lucode': u'1',
    u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/scenario_residential',
    }

if __name__ == '__main__':
    cat = get_cat()
    print "Removing workspace(s)" 
    for ws in cat.get_workspaces():
        if ws.name[:5] == "user-":
            print "\t%s" % ws.name                
            cat.delete(ws, recurse=True)
        
    csv_path = "/home/mlacayo/workspace/cas/data/output/sed_retent.csv"
    
    job_queue = [] #(priority, process, args, uploads, msg)
    
    ###run the SDR baseline with 3 differnt threshold flow accumulations

    #create a list of the test flows
    test_flows = [500, 1000, 1500]

    #set constants for outputs
    retention_field = "sed_retent"
    id_field = "ws_id"

    #get driver to read shapefiles
    driver = osgeo.ogr.GetDriverByName("ESRI Shapefile")    

    #create dictionary to store results
    retention_dict = {}

    #run SDR for each flow value and get retention from watershed 1
    for flow in test_flows:

        #copy SDR parameters template
        args = copy.copy(sdr_base_args)
        
        #set unique output directory based on flow value
        args[u'workspace_dir'] = args[u'workspace_dir'] + "_" + str(flow)

        #set the flow value
        args[u'threshold_flow_accumulation'] = flow
        #print "Running SDR with flow", flow

        #run SDR with the current parameters
        #natcap.invest.sdr.execute(args)

        ws = make_named_workspace()

        layer_name = ":".join([ws, "sdr"])

        uploads = {
            layer_name : os.path.join(args[u'workspace_dir'], u'watershed_results_sdr.shp')
        }
        
        job_queue.append([0,
                          natcap.invest.sdr.execute,
                          args,
                          uploads,
                          "Running SDR with flow %i" % flow])


        args = {
            "shapefile_path" : layer_url(layer_name),
            "key" : flow,
            "csv_path" : csv_path}

        uploads = {}

        job_queue.append([0,
                          extract_wrapper,
                          args,
                          uploads,
                          "Reading SDR results for flow %i" % flow])

    while len(job_queue) != 0:
        job = job_queue.pop(0)
        if not run_job(job):
            if job[0] < 2:
                job_queue.insert(0, job)
            else:
                job.append(job)

    ###select the retention closest to 9,000,000
    retention_dict = {}
    with open(csv_path, 'rb') as f:
        cf = csv.reader(f)
        for key, value in cf:
            retention_dict[int(key)] = float(value)

    #set constant for comparison
    target_retention = 9000000

    #create list to hold results
    comparison = []

    #calculate the suitability for each result
    for k in retention_dict.keys():
        #calculate the absolute difference between actual retention and the expected retention
        #store this value along with the associated flow value
        comparison.append([abs(retention_dict[k] - target_retention), k])

    #find the minimum difference and the associated flow value
    difference, target_flow = min(comparison)

    #print the result
    print "The closest result is achieved with flow", target_flow

    #modify the SDR template to have the ideal flow
    sdr_base_args[u'threshold_flow_accumulation'] = target_flow    



    ###run the proximity base scenario generator
    print "Generate scenario rasters"

    #generate the forest scenario LULC
    ws = make_named_workspace()

    forest_layer_name = ":".join([ws, "scenario"])

    uploads = {
        forest_layer_name : os.path.join(gen_forest_args[u'workspace_dir'], u'nearest_to_edge.tif')
    }
    
    job = [0, natcap.invest.scenario_gen_proximity.execute, gen_forest_args, uploads, "Generate forest scenario raster"]    
    job_queue.append(job)

    #generate the residential scenario LULC
    ws = make_named_workspace()

    residential_layer_name = ":".join([ws, "scenario"])

    uploads = {
        residential_layer_name : os.path.join(gen_residential_args[u'workspace_dir'], u'nearest_to_edge.tif')
    }
    
    job = [0, natcap.invest.scenario_gen_proximity.execute, gen_residential_args, uploads, "Generate residential scenario raster"]
    job_queue.append(job)

    ###run SDR for the scenarios
    print "Calculate SDR for scenarios"

    #create the SDR forest scenario dictionary
    sdr_forest_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_forest_args[u'workspace_dir'] = u'/home/mlacayo/workspace/cas/data/output/output/sdr_scenario_forest'

    #set the LULC to the scenario
    sdr_forest_args[u'lulc_path'] = cover_url(forest_layer_name)

    #run the SDR forest scenario
    ws = make_named_workspace()

    layer_name = ":".join([ws, "sdr"])

    uploads = {
        layer_name : os.path.join(sdr_forest_args[u'workspace_dir'], u'watershed_results_sdr.shp')
    }
    
    job = [0, natcap.invest.sdr.execute, sdr_forest_args, uploads, "Calculate SDR for forest scenario"]
    job_queue.append(job)

    #create the SDR residential scenario dictionary
    sdr_residential_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_residential_args[u'workspace_dir'] = u'/home/mlacayo/workspace/cas/data/output/output/sdr_scenario_residential'

    #set the LULC to the scenario
    sdr_residential_args[u'lulc_path'] = cover_url(residential_layer_name)

    #run the SDR residential scenario
    ws = make_named_workspace()

    layer_name = ":".join([ws, "sdr"])

    uploads = {
        layer_name : os.path.join(sdr_residential_args[u'workspace_dir'], u'watershed_results_sdr.shp')
    }

    
    job = [0, natcap.invest.sdr.execute, sdr_residential_args, uploads, "Calculate SDR for residential scenario"]
    job_queue.append(job)

    while len(job_queue) != 0:
        job = job_queue.pop(0)
        if not run_job(job):
            if job[0] < 2:
                job_queue.insert(0, job)
            else:
                job.append(job)
