import geoserver.catalog
import os.path

rest_url = "http://localhost:8080/gs215/rest"
username = "admin"
password = "geoserver"

data_path = "/home/esws/data"
data_stores = [("fresh_ws", os.path.join(data_path, "Base_Data/Freshwater/watersheds"))]


coverage_stores = [("freshwater_lulc_90", os.path.join(data_path, "Base_Data/Freshwater/landuse_90.tif")),                   
                   (None, os.path.join(data_path, "Base_Data/Freshwater/precip.tif")),
                   (None, os.path.join(data_path, "Base_Data/Freshwater/depth_to_root_rest_layer.tif")),                   
                   (None, os.path.join(data_path, "Base_Data/Freshwater/eto.tif")),
                   ("freshwater_pawc", os.path.join(data_path, "Base_Data/Freshwater/pawc.tif"))]
                   
workspace_name = "invest"
workspace_url = "http://esws.unige.ch"

cat = geoserver.catalog.Catalog(rest_url, username, password)

workspace = cat.get_workspace(workspace_name)
if workspace is None:
    workspace = cat.create_workspace(workspace_name, workspace_url)
else:
    cat.delete(workspace, recurse=True)
    workspace = cat.create_workspace(workspace_name, workspace_url)



for data_store_name, data_store_path in data_stores:
    print "Processing store %s" % data_store_name

    shapefile_plus_sidecars = {}
    for key in ["shp", "shx", "prj", "dbf"]:
        shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

    ft = cat.create_featurestore(data_store_name, workspace=workspace, data=shapefile_plus_sidecars)
    
for coverage_store_name, coverage_store_path in coverage_stores:
    if coverage_store_name is None:
        coverage_store_name, _ = os.path.splitext(os.path.basename(coverage_store_path))
    print "Processing store %s" % coverage_store_name

    tiffdata = { 'tiff' : coverage_store_path }

    c = cat.create_coveragestore(name = coverage_store_name,
                                 path = "file://" + coverage_store_path,
                                 workspace = workspace,
                                 layer_name = coverage_store_name)

#isinstance(resource, geoserver.resource.Coverage)
#isinstance(resource, geoserver.resource.FeatureType)

##for l in cat.get_layers():
##    print l.name
