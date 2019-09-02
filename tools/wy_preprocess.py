import os
#import sys
import argparse
import ogr2ogr
import osgeo.ogr


def main(args):
  print("Dissolving AOI")
  name, ext = os.path.splitext(os.path.basename(args.aoi))  
  ws = os.path.dirname(args.aoi)
  aoi_dissolve = os.path.join(ws,"aoi_union.shp")
  ogr2ogr_args = ["", aoi_dissolve, args.aoi, "-dialect", "sqlite", "-sql", "\"SELECT ST_Union(geometry) FROM " + name + "\""]

  #ogr2ogr.main(["","--version"])

  print("%s %s" % ("ogr2ogr", osgeo.ogr.GeneralCmdLineProcessor(ogr2ogr_args)))
  ogr2ogr.main(ogr2ogr_args)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Preprocessor for InVEST WY using global layers and a projected AOI')
  parser.add_argument('aoi',
                      help='AOI shapefile with a linear unit projection')

  try:
    args = parser.parse_args()
  except SystemExit:
    #print(sys.exc_info()[0])
    args = argparse.Namespace(aoi="/home/mlacayo/workspace/data_esws/data/Base_Data/Freshwater/watersheds.shp")

  main(args)
