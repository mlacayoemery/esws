import copy

import natcap.invest.scenario_gen_proximity
import natcap.invest.sdr

import osgeo.ogr
import os

import geoserver.catalog
import uuid

import csv

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
   
data_path = "/home/mlacayo/workspace/cas/data"

#http://127.0.0.1:8080/geoserver/cas/wms?service=WMS&version=1.1.0&request=GetMap&layers=cas:eto&styles=&bbox=444900.9029974863,4900407.170489954,485070.9029974863,4956627.170489954&width=548&height=768&srs=EPSG:26910&format=image%2Fgeotiff
#http://127.0.0.1:8080/geoserver/cas/wcs?service=WCS&version=1.0.0&request=GetCoverage&coverage=cas:eto&bbox=444900.9029974863,4900407.170489954,485070.9029974863,4956627.170489954&width=548&height=768&crs=EPSG:26910&format=image%2Fgeotiff

sdr_base_args = {
    u'biophysical_table_path': u'/home/mlacayo/workspace/cas/data/biophysical_table.csv',
    u'dem_path': u'/home/mlacayo/workspace/cas/data/dem.tif',
    u'drainage_path': u'',
    u'erodibility_path': u'/home/mlacayo/workspace/cas/data/erodibility.tif',
    u'erosivity_path': u'/home/mlacayo/workspace/cas/data/erosivity.tif',
    u'ic_0_param': u'0.5',
    u'k_param': u'2',
    u'lulc_path': u'/home/mlacayo/workspace/cas/data/landuse_90.tif',
    u'sdr_max': u'0.8',
    u'threshold_flow_accumulation': u'1000',
    u'watersheds_path': u'/home/mlacayo/workspace/cas/data/watersheds.shp',
    u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/sdr_base',
    }

#convert 50,000 HA (~36%) of pasture (type 80) to conifers (type 56)
#when it is near any age conifers (types 56, 57, 58, 59, 60, 61)
gen_forest_args = {
    u'aoi_path': u'',
    u'area_to_convert': u'50000',
    u'base_lulc_path': u'/home/mlacayo/workspace/cas/data/landuse_90.tif',
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
    u'base_lulc_path': u'/home/mlacayo/workspace/cas/data/landuse_90.tif',
    u'convert_farthest_from_edge': False,
    u'convert_nearest_to_edge': True,
    u'convertible_landcover_codes': u'80',
    u'focal_landcover_codes': u'1 2 3 4',
    u'n_fragmentation_steps': u'1',
    u'replacment_lucode': u'1',
    u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/scenario_residential',
    }

if __name__ == '__main__':
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
        #print "Runing SDR with flow", flow

        #run SDR with the current parameters
        #natcap.invest.sdr.execute(args)

        ws = make_named_workspace()
        
        job_queue.append((0,
                          natcap.invest.sdr.execute,
                          args,
                          {
                              ":".join([ws, "sdr"]) : os.path.join(args[u'workspace_dir'], u'watershed_results_sdr.shp')
                          },
                          "Runing SDR with flow %i" % flow))

        job_queue.append((0,
                          extract_wrapper,
                          {"shapefile_path" : os.path.join(args[u'workspace_dir'],
                                                           u'watershed_results_sdr.shp'),
                           "key" : flow,
                           "csv_path" : csv_path},
                          {},
                          "Reading SDR results for flow %i" % flow))

    while len(job_queue) != 0:
        job = job_queue.pop()
        _, p, args, uploads, msg = job
        if local_parameters(args):
            print msg
            apply(p, [args])
            for layer_name, layer_path in uploads.iteritems():
                print "Publishing %s" % layer_name
                ws, layer_name = layer_name.split(":")
                publish_shp(layer_path, layer_name, ws)
        else:
            job_queue.append(job)


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
    print "Generate forest scenario raster"
    natcap.invest.scenario_gen_proximity.execute(gen_forest_args)

    #generate the residential scenario LULC
    print "Generate residential scenario raster"
    natcap.invest.scenario_gen_proximity.execute(gen_residential_args)



    ###run SDR for the scenarios
    print "Calculate SDR for scenarios"

    #create the SDR forest scenario dictionary
    sdr_forest_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_forest_args[u'workspace_dir'] = u'/home/mlacayo/workspace/cas/data/output/output/sdr_scenario_forest'

    #set the LULC to the scenario
    sdr_forest_args[u'lulc_path'] = u'/home/mlacayo/workspace/cas/data/output/output/scenario_forest/nearest_to_edge.tif'

    #run the SDR forest scenario
    print "Calculate SDR for forest scenario"
    natcap.invest.sdr.execute(sdr_forest_args)

    #create the SDR residential scenario dictionary
    sdr_residential_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_residential_args[u'workspace_dir'] = u'/home/mlacayo/workspace/cas/data/output/output/sdr_scenario_residential'

    #set the LULC to the scenario
    sdr_residential_args[u'lulc_path'] = u'/home/mlacayo/workspace/cas/data/output/output/scenario_residential/nearest_to_edge.tif'

    #run the SDR residential scenario
    print "Calculate SDR for residential scenario"
    natcap.invest.sdr.execute(sdr_residential_args)

    
