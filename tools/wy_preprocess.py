#https://gis.stackexchange.com/questions/39080/using-ogr2ogr-to-convert-gml-to-shapefile-in-python

import ogr2ogr

def main():
  #note: main is expecting sys.argv, where the first argument is the script name
  #so, the argument indices in the array need to be offset by 1
  ogr2ogr.main(["","-f", "KML", "out.kml", "data/san_andres_y_providencia_administrative.shp"])
