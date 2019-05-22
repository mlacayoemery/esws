import requests

wps_server_url = "http://127.0.0.1:8080/gs215/ows"
post_data = {"service" : "WPS",
             "version" : "1.0.0",
             "request" : "GetCapabilities"}

ch_centroid = {"type":"FeatureCollection",
               "features":[{"type":"Feature",
                            "geometry":{"type":"Point",
                                        "coordinates":[8.2319,
                                                       46.8011]}}],
               "crs":{"type":"name",
                      "properties":{"name":"urn:ogc:def:crs:EPSG::4326"}}}


r = requests.post(wps_server_url, post_data)
print("WPS GetCapabilities status %i" % r.status_code)

if r.ok:
    post_data = {"service" : "WPS",
                 "version" : "1.0.0",
                 "request" : "DescribeProcess",
                 "identifier" : "vec:Count"}

    r = requests.post(wps_server_url, post_data)
    print("WPS DescribeProcess status %i" % r.status_code)


##if r.ok:
##    post_data = {"service" : "WPS",
##                 "version" : "1.0.0",
##                 "request" : "DescribeProcess",
##                 "identifier" : "vec:Count",
##                 "datainputs" : {"identifier" : "features",
##                                 "data" : {"complexdata" : "<![CDATA[%s]]>" % ch_centroid}}}
##
##    r = requests.post(wps_server_url, json = post_data)
##    print("WPS Execute status %i" % r.status_code)
