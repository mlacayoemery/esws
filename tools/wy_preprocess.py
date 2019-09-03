import os
import argparse
import osgeo.gdal

def dissolve(in_path, out_path):
  name, ext = os.path.splitext(os.path.basename(in_path))
  srcDS = osgeo.gdal.OpenEx(in_path)
  ds = osgeo.gdal.VectorTranslate(out_path, srcDS, SQLStatement="SELECT ST_Union(geometry) FROM %s" % name , SQLDialect='sqlite')

def buffer(in_path, out_path, units):
  name, ext = os.path.splitext(os.path.basename(in_path))
  srcDS = osgeo.gdal.OpenEx(in_path)
  ds = osgeo.gdal.VectorTranslate(out_path, srcDS, SQLStatement="SELECT ST_Buffer(geometry, %f) FROM %s" % (units, name) , SQLDialect='sqlite')
  

def transform(in_path, out_path, dstSRS=4326):
  name, ext = os.path.splitext(os.path.basename(in_path))
  srcDS = osgeo.gdal.OpenEx(in_path)
  ds = osgeo.gdal.VectorTranslate(out_path, srcDS, dstSRS="EPSG:%i" % dstSRS, SQLStatement="SELECT ST_Transform(geometry, %i) FROM %s" % (dstSRS, name) , SQLDialect='sqlite')
  #ds = osgeo.gdal.VectorTranslate(out_path, srcDS, dstSRS="EPSG:%i" % dstSRS, reproject=True)
  
def cut_warp(in_raster_path, out_raster_path, vector_path, wkt):
  ds = osgeo.gdal.Warp(out_raster_path,
                       in_raster_path,
                       format='GTiff',
                       dstSRS=wkt,
                       cutlineDSName=vector_path,
                       cropToCutline=True,
                       creationOptions=["COMPRESS=LZW"])
  #ds = osgeo.gdal.Warp(out_raster_path, in_raster_path, format='GTiff')
  
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Preprocessor for InVEST WY using global layers and a projected AOI')
  parser.add_argument('aoi',
                      help='AOI shapefile with a linear unit projection')
  parser.add_argument('lulc',
                      help='Global LULC in EPSG:4326')

  try:
    args = parser.parse_args()
    aoi = args.aoi
    lulc_4326 = args.lulc
  except SystemExit:
    aoi = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/watersheds.shp"
    depth_4326 = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/depth_to_root_rest_layer.tif"
    eto_4326 = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/eto.tif"
    lulc_4326 = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/landuse_90.tif"
    pawc_4326 = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/pawc.tif"
    precip_4326 = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/precip.tif"

  ds = osgeo.gdal.OpenEx(aoi, osgeo.gdal.OF_VECTOR)
  wkt = ds.GetLayer().GetSpatialRef().ExportToWkt()
  ds = None

  wy_aoi = os.path.join(os.path.dirname(aoi),"wy_aoi.shp")
  wy_aoi_buffer = os.path.join(os.path.dirname(aoi),"wy_buffer.shp")
  wy_aoi_buffer_4326 = os.path.join(os.path.dirname(aoi),"wy_aoi_buffer_4326.shp")

  depth_aoi = os.path.join(os.path.dirname(lulc_4326),"wy_depth_aoi.tif")
  eto_aoi = os.path.join(os.path.dirname(lulc_4326),"wy_eto_aoi.tif")
  lulc_aoi = os.path.join(os.path.dirname(lulc_4326),"wy_lulc_aoi.tif")
  pawc_aoi = os.path.join(os.path.dirname(lulc_4326),"wy_pawc_aoi.tif")
  precip_aoi = os.path.join(os.path.dirname(lulc_4326),"wy_precip_aoi.tif")

  assert aoi not in [wy_aoi,
                     wy_aoi_buffer,
                     wy_aoi_buffer_4326]

  #preprocess AOI
  dissolve(aoi, wy_aoi)
  buffer(wy_aoi, wy_aoi_buffer, 5000)
  transform(wy_aoi_buffer, wy_aoi_buffer_4326, 4326)

  #preprocess rasters
  cut_warp(depth_4326, depth_aoi, aoi, wkt)
  cut_warp(eto_4326, eto_aoi, aoi, wkt)
  cut_warp(lulc_4326, lulc_aoi, aoi, wkt)
  cut_warp(pawc_4326, pawc_aoi, aoi, wkt)
  cut_warp(precip_4326, precip_aoi, aoi, wkt)
