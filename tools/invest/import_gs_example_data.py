import geoserver.catalog
import os.path

rest_url = "http://localhost:8080/gs213/rest"
username = "admin"
password = "geoserver"

data_path = "/home/mlacayo/workspace/cas/data"
data_stores = [("watersheds", os.path.join(data_path, "watersheds"))]

coverage_stores = [(None, os.path.join(data_path, "dem.tif")),
                   (None, os.path.join(data_path, "depth_to_root_rest_layer.tif")),
                   (None, os.path.join(data_path, "erodibility.tif")),
                   (None, os.path.join(data_path, "erosivity.tif")),
                   (None, os.path.join(data_path, "eto.tif")),
                   (None, os.path.join(data_path, "landuse_90.tif"))]



workspace_name = "cas"
workspace_url = "http://www.unige.ch"

cat = geoserver.catalog.Catalog(rest_url, username, password)

print "Removing workspace(s)" 
for ws in cat.get_workspaces():
    if ws.name[:3] == "cas":
        print "\t%s" % ws.name                
        cat.delete(ws, recurse=True)

workspace = cat.get_workspace(workspace_name)
if workspace is None:
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

    c = cat.create_coveragestore_external_geotiff(coverage_store_name, "file://" + coverage_store_path, workspace)
