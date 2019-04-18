import logging
import sys
import os

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    p = path.dirname(path.dirname(path.abspath(__file__)))
    print(p)
    sys.path.append(p)

import easyows
import gdaltools

import copy

sys.path.append("/home/mlacayo/workspace/invest/src/natcap/invest/pygeoprocessing_0_3_3")

import natcap.invest.scenario_gen_proximity
import natcap.invest.sdr

import csv

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logger = logging.getLogger("gsows")
##    handler = logging.StreamHandler(sys.stdout)
##    handler.setLevel(logging.DEBUG)
##    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
##    handler.setFormatter(formatter)    
##    logger.addHandler(handler)

    logger.info("Starting GS OWS example.")
    
    cat = easyows.Catalog(gs_url = "http://localhost:8080/geoserver",
                          username = "admin",
                          password = "geoserver",
                          ws_prefix = "user-")

    
    logger.info("Removing workspace(s)")
    cat.clean_named_workspace()

    data_path = "/home/mlacayo/workspace/cas/data"

    sdr_base_args = {
        u'biophysical_table_path': u'/home/mlacayo/workspace/cas/data/biophysical_table.csv',
        u'dem_path': cat.cover_url("cas:dem"),
        u'drainage_path': u'',
        u'erodibility_path': cat.cover_url("cas:erodibility"),
        u'erosivity_path': cat.cover_url("cas:erosivity"),
        u'ic_0_param': u'0.5',
        u'k_param': u'2',
        u'lulc_path': cat.cover_url("cas:landuse_90"),
        u'sdr_max': u'0.8',
        u'threshold_flow_accumulation': u'1000',
        u'watersheds_path': cat.layer_url("cas:watersheds"),
        u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/sdr_base',
        }

    #convert 50,000 HA (~36%) of pasture (type 80) to conifers (type 56)
    #when it is near any age conifers (types 56, 57, 58, 59, 60, 61)
    gen_forest_args = {
        u'aoi_path': u'',
        u'area_to_convert': u'50000',
        u'base_lulc_path': cat.cover_url("cas:landuse_90"),
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
        u'base_lulc_path': cat.cover_url("cas:landuse_90"),
        u'convert_farthest_from_edge': False,
        u'convert_nearest_to_edge': True,
        u'convertible_landcover_codes': u'80',
        u'focal_landcover_codes': u'1 2 3 4',
        u'n_fragmentation_steps': u'1',
        u'replacment_lucode': u'1',
        u'workspace_dir': u'/home/mlacayo/workspace/cas/data/output/output/scenario_residential',
        }

       
    csv_path = "/home/mlacayo/workspace/cas/data/output/sed_retent.csv"
    
    job_queue = []
    
    ###run the SDR baseline with 3 differnt threshold flow accumulations

    #create a list of the test flows
    test_flows = [500, 1000, 1500]

    #set constants for outputs
    retention_field = "sed_retent"
    id_field = "ws_id"

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
        #print("Running SDR with flow", flow)

        #run SDR with the current parameters
        #natcap.invest.sdr.execute(args)

        ws = cat.make_named_workspace()

        layer_name = ":".join([ws, "sdr"])

        uploads = {
            layer_name : os.path.join(args[u'workspace_dir'], u'watershed_results_sdr.shp')
        }
        
        job_queue.append(easyows.Job(natcap.invest.sdr.execute,
                                     args,
                                     uploads,
                                     "Running SDR with flow %i" % flow,
                                     0,
                                     cat))


        args = {
            "shapefile_path" : cat.layer_url(layer_name),
            "key" : flow,
            "csv_path" : csv_path}

        uploads = {}

        job_queue.append(easyows.Job(gdaltools.extract_wrapper,
                                     args,
                                     uploads,
                                     "Reading SDR results for flow %i" % flow,
                                     0,
                                     cat))

    while len(job_queue) != 0:
        job = job_queue.pop(0)
        if not job.run():
            job_queue.insert(0, job)

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
    print("The closest result is achieved with flow", target_flow)

    #modify the SDR template to have the ideal flow
    sdr_base_args[u'threshold_flow_accumulation'] = target_flow    



    ###run the proximity base scenario generator
    print("Generate scenario rasters")

    #generate the forest scenario LULC
    ws = cat.make_named_workspace()

    forest_layer_name = ":".join([ws, "scenario"])

    uploads = {
        forest_layer_name : os.path.join(gen_forest_args[u'workspace_dir'], u'nearest_to_edge.tif')
    }
    
    job = easyows.Job(natcap.invest.scenario_gen_proximity.execute,
                      gen_forest_args,
                      uploads,
                      "Generate forest scenario raster",
                      0,
                      cat)
    job_queue.append(job)

    #generate the residential scenario LULC
    ws = cat.make_named_workspace()

    residential_layer_name = ":".join([ws, "scenario"])

    uploads = {
        residential_layer_name : os.path.join(gen_residential_args[u'workspace_dir'], u'nearest_to_edge.tif')
    }
    
    job = easyows.Job(natcap.invest.scenario_gen_proximity.execute,
                      gen_residential_args,
                      uploads,
                      "Generate residential scenario raster",
                      0,
                      cat)
    job_queue.append(job)

    ###run SDR for the scenarios
    print("Calculate SDR for scenarios")

    #create the SDR forest scenario dictionary
    sdr_forest_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_forest_args[u'workspace_dir'] = u'/home/mlacayo/workspace/cas/data/output/output/sdr_scenario_forest'

    #set the LULC to the scenario
    sdr_forest_args[u'lulc_path'] = cat.cover_url(forest_layer_name)

    #run the SDR forest scenario
    ws = cat.make_named_workspace()

    layer_name = ":".join([ws, "sdr"])

    uploads = {
        layer_name : os.path.join(sdr_forest_args[u'workspace_dir'], u'watershed_results_sdr.shp')
    }
    
    job = easyows.Job(natcap.invest.sdr.execute,
                      sdr_forest_args,
                      uploads,
                      "Calculate SDR for forest scenario",
                      0,
                      cat)
    job_queue.append(job)

    #create the SDR residential scenario dictionary
    sdr_residential_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_residential_args[u'workspace_dir'] = u'/home/mlacayo/workspace/cas/data/output/output/sdr_scenario_residential'

    #set the LULC to the scenario
    sdr_residential_args[u'lulc_path'] = cat.cover_url(residential_layer_name)

    #run the SDR residential scenario
    ws = cat.make_named_workspace()

    layer_name = ":".join([ws, "sdr"])

    uploads = {
        layer_name : os.path.join(sdr_residential_args[u'workspace_dir'], u'watershed_results_sdr.shp')
    }

    
    job = easyows.Job(natcap.invest.sdr.execute,
                      sdr_residential_args,
                      uploads,
                      "Calculate SDR for residential scenario",
                      0,
                      cat)
    job_queue.append(job)

    while len(job_queue) != 0:
        job = job_queue.pop(0)
        if not job.run():
            job_queue.insert(0, job)


    logger.info("Complete")
