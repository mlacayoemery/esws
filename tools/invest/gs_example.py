import copy

import natcap.invest.scenario_gen_proximity
import natcap.invest.sdr

import osgeo.ogr
import os

sdr_base_args = {
    u'biophysical_table_path': u'D:/invest/input/biophysical_table.csv',
    u'dem_path': u'D:/invest/input/dem.tif',
    u'drainage_path': u'',
    u'erodibility_path': u'D:/invest/input/erodibility.tif',
    u'erosivity_path': u'D:/invest/input/erosivity.tif',
    u'ic_0_param': u'0.5',
    u'k_param': u'2',
    u'lulc_path': u'D:/invest/input/landuse_90.tif',
    u'sdr_max': u'0.8',
    u'threshold_flow_accumulation': u'1000',
    u'watersheds_path': u'D:/invest/input/watersheds.shp',
    u'workspace_dir': u'D:/invest/output/sdr_base',
    }

#convert 50,000 HA (~36%) of pasture (type 80) to conifers (type 56)
#when it is near any age conifers (types 56, 57, 58, 59, 60, 61)
gen_forest_args = {
    u'aoi_path': u'',
    u'area_to_convert': u'50000',
    u'base_lulc_path': u'D:/invest/input/landuse_90.tif',
    u'convert_farthest_from_edge': False,
    u'convert_nearest_to_edge': True,
    u'convertible_landcover_codes': u'80',
    u'focal_landcover_codes': u'56 57 58 59 60 61',
    u'n_fragmentation_steps': u'1',
    u'replacment_lucode': u'56',
    u'workspace_dir': u'D:/invest/output/scenario_forest',
    }

#convert 50,000 HA (~36%) of pasture (type 80) to low density residential (type 1)
#when it is near any density residential (types 1, 2, 3 4)
gen_residential_args = {
    u'aoi_path': u'',
    u'area_to_convert': u'50000',
    u'base_lulc_path': u'D:/invest/input/landuse_90.tif',
    u'convert_farthest_from_edge': False,
    u'convert_nearest_to_edge': True,
    u'convertible_landcover_codes': u'80',
    u'focal_landcover_codes': u'1 2 3 4',
    u'n_fragmentation_steps': u'1',
    u'replacment_lucode': u'1',
    u'workspace_dir': u'D:/invest/output/scenario_residential',
    }

if __name__ == '__main__':
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
        print "Runing SDR with flow", flow

        #run SDR with the current parameters
        natcap.invest.sdr.execute(args)



        ###read the results from the SDR runs

        #set the path for the output results
        shapefile_path = args[u'workspace_dir']
        shapefile_path = os.path.join(shapefile_path, u'watershed_results_sdr.shp')

        #open the output results
        data_source = driver.Open(shapefile_path, 0)

        #get the actual data from the results
        layer = data_source.GetLayer()

        #loop over each feature in the data
        for feature in layer:

            #check if watershed 1 found
            if feature.GetField(id_field) == 1:

                #save retention
                retention_dict[flow] = feature.GetField(retention_field)

        #close the results
        dataSource = None



    ###select the retention closest to 9,000,000

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

    #generate the forest scenario LULC
    natcap.invest.scenario_gen_proximity.execute(gen_forest_args)

    #generate the residential scenario LULC
    natcap.invest.scenario_gen_proximity.execute(gen_residential_args)



    ###run SDR for the scenarios

    #create the SDR forest scenario dictionary
    sdr_forest_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_forest_args[u'workspace_dir'] = u'D:/invest/output/sdr_scenario_forest'

    #set the LULC to the scenario
    sdr_forest_args[u'lulc_path'] = u'D:/invest/output/scenario_forest/nearest_to_edge.tif'

    #run the SDR forest scenario
    natcap.invest.sdr.execute(sdr_forest_args)

    #create the SDR residential scenario dictionary
    sdr_residential_args = copy.copy(sdr_base_args)

    #set the worspace directory
    sdr_residential_args[u'workspace_dir'] = u'D:/invest/output/sdr_scenario_residential'

    #set the LULC to the scenario
    sdr_residential_args[u'lulc_path'] = u'D:/invest/output/scenario_residential/nearest_to_edge.tif'

    #run the SDR residential scenario
    natcap.invest.sdr.execute(sdr_residential_args)

    
