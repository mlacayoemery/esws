import geoserver.catalog
cat = geoserver.catalog.Catalog("http://gala.unige.ch:8080/geoserver/rest", "admin", "geoserver")
for l in cat.get_layers():
    print l.name
