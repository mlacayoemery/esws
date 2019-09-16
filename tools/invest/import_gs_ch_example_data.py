import geoserver.catalog
import os.path

rest_url = "http://localhost:8080/gs215/rest"
username = "admin"
password = "geoserver"

data_path = "/home/esws/data/ch"
data_stores = [("ch_basins", os.path.join(data_path, "hybas_eu_lev07_v1c_CH_2056"))]

coverage_stores = [("ch_depth", os.path.join(data_path, "wy_depth_aoi.tif")),
                   ("ch_pawc", os.path.join(data_path, "wy_pawc_aoi.tif")),
                   ("ch_precip", os.path.join(data_path, "wy_precip_aoi.tif")),
                   ("ch_eto", os.path.join(data_path, "wy_eto_aoi.tif")),
                   ("ch_lulc", os.path.join(data_path, "wy_lulc_aoi.tif"))]



workspace_name = "cas"
workspace_url = "http://www.unige.ch"

cat = geoserver.catalog.Catalog(rest_url, username=username, password=password)

print("Removing workspace(s)")
for ws in cat.get_workspaces():
    if ws.name[:3] == "swatch21":
        print("\t%s" % ws.name)
        cat.delete(ws, recurse=True)

workspace = cat.get_workspace(workspace_name)
if workspace is None:
    workspace = cat.create_workspace(workspace_name, workspace_url)

for data_store_name, data_store_path in data_stores:
    print("Processing store %s" % data_store_name)

    shapefile_plus_sidecars = {}
    for key in ["shp", "shx", "prj", "dbf"]:
        shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

    ft = cat.create_featurestore(data_store_name, workspace=workspace, data=shapefile_plus_sidecars)
    
for coverage_store_name, coverage_store_path in coverage_stores:
    if coverage_store_name is None:
        coverage_store_name, _ = os.path.splitext(os.path.basename(coverage_store_path))
    print("Processing store %s" % coverage_store_name)

    tiffdata = { 'tiff' : coverage_store_path }

    c = cat.create_coveragestore(coverage_store_name,
                                 workspace = workspace,
                                 path = "file://" + coverage_store_path,
                                 layer_name = coverage_store_name)
