import osgeo.ogr
import os

driver = osgeo.ogr.GetDriverByName("ESRI Shapefile")   

import csv

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
