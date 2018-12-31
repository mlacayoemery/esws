import owslib.wps
import owslib.etree

import xml.etree.ElementTree
import xml.dom.minidom

import lxml.etree

import urllib.request

geoserver = "http://127.0.0.1:8080"
list_capabilities = False
list_processes = False
describe_processes = ["JTS:area"]
test_processid = "geo:centroid"

wps_url = geoserver + "/geoserver/ows"
wps = owslib.wps.WebProcessingService(wps_url, verbose=False, skip_caps=True)


if list_capabilities:
    wps.getcapabilities()
    print (wps.identification.type)
    print (wps.identification.title)

    for operation in wps.operations:
        print(operation.name)

    for process in wps.processes:
        print ("%s - %s" % (process.identifier, process.title))

if list_processes:
    for process_name in processes:
        process = wps.describeprocess(process_name)

        print ("%s - %s" % (process.identifier, process.title))
        print ("\n%s\n" % process.abstract)

        
        for parameter in process.dataInputs:
            print ("INPUTS")
            owslib.wps.printInputOutput(parameter)
            print ([parameter.identifier, parameter.title, parameter.abstract, parameter.dataType, parameter.minOccurs, parameter.maxOccurs])

        for output in process.processOutputs:
            print ("OUTPUTS")
            owslib.wps.printInputOutput(output)        



processid = test_processid
print ("\nTesting standard process %s" % processid)
polygon = [(-102.8184, 39.5273), (-102.8184, 37.418), (-101.2363, 37.418), (-101.2363, 39.5273), (-102.8184, 39.5273)]
featureCollection = owslib.wps.GMLMultiPolygonFeatureCollection( [polygon] )


#print ("\n",xml.etree.ElementTree.dump(featureCollection.getXml()),"\n")

inputs = [ ("geom", featureCollection)]
output = "OUTPUT"

request=None
#request = xml.etree.ElementTree.fromstring(open("JTS_area_WKT.xml").read())
#request = open("JTS_area_WKT.xml").read()
#request = "file:///home/mlacayo/workspace/wpsclient/django/wpsclient/JTS_area_WKT.xml"

#print ("Line 56")
    
execution = wps.execute(processid, inputs, output = "OUTPUT", request=request)
#print (xml.dom.minidom.parseString(execution.request).toprettyxml())

try:
    owslib.wps.monitorExecution(execution)
except lxml.etree.XMLSyntaxError as e:
    print (e)


print ("\nTesting modified XML request for process %s" % processid)
##request_file = open("JTS_area_WKT.xml", "rb")
##xml_data = request_file.read()
##r = urllib.request.Request(
##    "http://127.0.0.1:8080/geoserver/wps",
##    data=xml_data,
##    headers={
##        'Content-Type': 'application/xml',
##        #'Accept' : 'image/tiff'
##        })
##
##u = urllib.request.urlopen(r)
##
##print (u.read())

execution = owslib.wps.WPSExecution(version="1.0.0",
                                    url= geoserver + "/geoserver/ows",
                                    username=None,
                                    password=None,
                                    verbose=False)

requestElement = execution.buildRequest(processid,
                                        inputs)#,
                                        #output)


#http://127.0.0.1:8080/geoserver/sf/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=sf:restricted&maxFeatures=1&outputFormat=gml3
##  <wps:DataInputs>
##    <wps:Input>
##      <ows:Identifier>geom</ows:Identifier>
##      <wps:Reference mimeType="text/xml; subtype=gml/3.1.1" xlink:href="http://127.0.0.1:8080/geoserver/sf/ows?service=WFS&amp;version=1.0.0&amp;request=GetFeature&amp;typeName=sf:restricted&amp;maxFeatures=1&amp;outputFormat=gml3" method="GET"/>
##    </wps:Input>
##  </wps:DataInputs>

ResponseForm="""
  <wps:ResponseForm>
    <wps:RawDataOutput mimeType="application/gml-3.1.1">
      <ows:Identifier>result</ows:Identifier>
    </wps:RawDataOutput>
  </wps:ResponseForm>"""


##ResponseForm = xml.etree.ElementTree.Element("wps100:ResponseForm")
##RawDataOutput = xml.etree.ElementTree.SubElement(ResponseForm, "wps100:RawDataOutput")
##RawDataOutput.set("mimeType","application/gml-3.1.1")
##Identifier = xml.etree.ElementTree.SubElement(RawDataOutput, "ows110:Identifier")
##Identifier.text = "result"

ns = {'wps100': 'http://www.opengis.net/wps/1.0.0',
      'ows110': 'http://www.opengis.net/ows/1.1'}

ResponseForm = lxml.etree.Element("{http://www.opengis.net/wps/1.0.0}ResponseForm")
RawDataOutput = lxml.etree.SubElement(ResponseForm, "{http://www.opengis.net/wps/1.0.0}RawDataOutput")
RawDataOutput.set("mimeType","application/gml-3.1.1")
Identifier = lxml.etree.SubElement(RawDataOutput, "{http://www.opengis.net/ows/1.1}Identifier")
Identifier.text = "result"


#Execute = requestElement.find("wps100:Execute", ns)

requestElement.append(ResponseForm)

print (xml.dom.minidom.parseString(owslib.etree.etree.tostring(requestElement)).toprettyxml())

##ResponseForm = xml.etree.ElementTree.fromstring(ResponseForm)
##
##request = owslib.etree.etree.tostring(requestElement)
##
##execution.request = request
##
##print("Line 101")
##print (xml.dom.minidom.parseString(owslib.etree.etree.tostring(requestElement)).toprettyxml())

request = owslib.etree.etree.tostring(requestElement)
execution = wps.execute(processid, inputs, output = "OUTPUT", request=request)
#print (xml.dom.minidom.parseString(execution.request).toprettyxml())
owslib.wps.monitorExecution(execution)

print ("\nManual request\n")
r = urllib.request.Request(
    geoserver + "/geoserver/wps",
    data=request,
    headers={
        'Content-Type': 'application/xml',
        #'Accept' : 'image/tiff'
        })

u = urllib.request.urlopen(r)

print (xml.dom.minidom.parseString(u.read()).toprettyxml())
