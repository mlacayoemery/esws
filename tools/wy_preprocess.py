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
  #ds = osgeo.gdal.VectorTranslate(out_path, srcDS, dstSRS="EPSG:%i" % dstSRS, SQLStatement="SELECT ST_Transform(geometry, %i) FROM %s" % (dstSRS, name) , SQLDialect='sqlite')
  ds = osgeo.gdal.VectorTranslate(out_path, srcDS, dstSRS="EPSG:%i" % dstSRS, reproject=True)

def select_touches(in_path, filter_path, out_path):
  #osgeo.gdal.VectorTranslate(layers = [])
  pass
  
def cut_warp(in_raster_path, out_raster_path, vector_path, wkt):
##  gdal_template = "gdalwarp -t_srs %s -cutline %s -of GTiff -co \"COMPRESS=DEFLATE\" -crop_to_cutline %s %s"
##  print(gdal_template % (wkt,vector_path,in_raster_path,out_raster_path))

  ds = osgeo.gdal.Warp(out_raster_path,
                       in_raster_path,
                       format='GTiff',
                       dstSRS=wkt,
                       cutlineDSName=vector_path,
                       cropToCutline=True,
                       creationOptions=["COMPRESS=DEFLATE"])
  #ds = osgeo.gdal.Warp(out_raster_path, in_raster_path, format='GTiff')

def raster_add(rasters=[]):
  #gdal_calc.py -A wc2.0_30s_prec_01.tif -B wc2.0_30s_prec_02.tif -C wc2.0_30s_prec_03.tif -D wc2.0_30s_prec_04.tif -E wc2.0_30s_prec_05.tif -F wc2.0_30s_prec_06.tif -G wc2.0_30s_prec_07.tif -H wc2.0_30s_prec_08.tif -I wc2.0_30s_prec_09.tif -J wc2.0_30s_prec_10.tif -K wc2.0_30s_prec_11.tif -L wc2.0_30s_prec_12.tif --outfile=wc2.0_30s_prec_00.tif --calc="A+B+C+D+E+F+G+H+I+J+K+L"
  #gdal_translate wc2.0_30s_prec_00.tif wc2.0_30s_prec.tif -co "COMPRESS=DEFLATE"
  osgeo.gdal.gdal_calc.doit()

global_path = "/home/mlacayo/workspace/data_esws/demo"
depth_4326 = ""
eto_4326 = os.path.join(global_path, "et0_yr_fix.tif")
lulc_4326 = os.path.join(global_path, "GLOBCOVER_L4_200901_200912_V2.3.tif")
pawc_4326 = ""
precip_4326 = os.path.join(global_path, "wc2.0_30s_prec.tif")
soil_4326 = os.path.join(global_path, "hwsd.bil")
 
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Preprocessor for InVEST WY using global layers and a projected AOI')
  parser.add_argument('aoi',
                      help='AOI shapefile with a linear unit projection')


  try:
    args = parser.parse_args()
    aoi = args.aoi
    
  except SystemExit:
    aoi = "/home/mlacayo/workspace/data_esws/demo/swissBOUNDARIES3D_1_3_TLM_LANDESGEBIET.shp"
    
  ds = osgeo.gdal.OpenEx(aoi, osgeo.gdal.OF_VECTOR)
  wkt = ds.GetLayer().GetSpatialRef().ExportToWkt()
  ds = None

  wy_aoi = os.path.join(os.path.dirname(aoi),"wy_aoi.shp")
  wy_aoi_buffer = os.path.join(os.path.dirname(aoi),"wy_buffer.shp")
  wy_aoi_buffer_4326 = os.path.join(os.path.dirname(aoi),"wy_aoi_buffer_4326.shp")

  depth_aoi = os.path.join(os.path.dirname(wy_aoi),"wy_depth_aoi.tif")
  eto_aoi = os.path.join(os.path.dirname(wy_aoi),"wy_eto_aoi.tif")
  lulc_aoi = os.path.join(os.path.dirname(wy_aoi),"wy_lulc_aoi.tif")
  pawc_aoi = os.path.join(os.path.dirname(wy_aoi),"wy_pawc_aoi.tif")
  precip_aoi = os.path.join(os.path.dirname(wy_aoi),"wy_precip_aoi.tif")

  assert aoi not in [wy_aoi,
                     wy_aoi_buffer,
                     wy_aoi_buffer_4326]

  #preprocess AOI
  print("Dissolving AOI")
  dissolve(aoi, wy_aoi)
  print("Buffering AOI")
  buffer(wy_aoi, wy_aoi_buffer, 5000)
  print("Creating AOI for clipping")
  transform(wy_aoi_buffer, wy_aoi_buffer_4326, 4326)

  #preprocess rasters
  print("Clipping rasters")

  #print ("Clipping soil depth")
  #cut_warp(depth_4326, depth_aoi, wy_aoi_buffer_4326, wkt)

  print("Clipping et0")
  cut_warp(eto_4326, eto_aoi, wy_aoi_buffer_4326, wkt)

  print("Clipping lulc")
  cut_warp(lulc_4326, lulc_aoi, wy_aoi_buffer_4326, wkt)

  #print("Clipping pawc")
  #cut_warp(pawc_4326, pawc_aoi, wy_aoi_buffer_4326, wkt)

  print ("Clipping precip")
  cut_warp(precip_4326, precip_aoi, wy_aoi_buffer_4326, wkt)
