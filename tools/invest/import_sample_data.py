import geoserver.catalog
cat = geoserver.catalog.Catalog("http://gala.unige.ch:8080/geoserver/rest", "admin", "geoserver")
for l in cat.get_layers():
    print l.name

#http://129.194.172.23/geoserver/wfs?typename=geonode%3Awatersheds&outputFormat=SHAPE-ZIP&version=1.0.0&service=WFS&request=GetFeature
#http://129.194.172.23/geoserver/wfs?typename=geonode%3Asubwatersheds&outputFormat=SHAPE-ZIP&version=1.0.0&service=WFS&request=GetFeature
#http://129.194.172.23/geoserver/wcs?format=image%2Ftiff&request=GetCoverage&version=2.0.1&service=WCS&coverageid=geonode%3Adem
