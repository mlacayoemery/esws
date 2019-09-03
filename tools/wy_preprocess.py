import os
#import sys
import argparse
import ogr2ogr
import osgeo.ogr
import osgeo.gdal

def dissolve(in_path, out_path):
  name, ext = os.path.splitext(os.path.basename(in_path))
  srcDS = osgeo.gdal.OpenEx(in_path)
  ds = osgeo.gdal.VectorTranslate(out_path, srcDS, SQLStatement="SELECT ST_Union(geometry) FROM " + name , SQLDialect='sqlite')

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Preprocessor for InVEST WY using global layers and a projected AOI')
  parser.add_argument('aoi',
                      help='AOI shapefile with a linear unit projection')

  try:
    args = parser.parse_args()
    aoi = args.aoi
  except SystemExit:
    aoi = "/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/watersheds.shp"

  wy_aoi = os.path.join(os.path.dirname(aoi),"wy_aoi.shp")
  assert wy_aoi != aoi
  dissolve(aoi, wy_aoi)
