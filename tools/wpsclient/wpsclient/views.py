import logging
import inspect

from django.shortcuts import render, get_object_or_404, redirect

from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS

from .models import ElementCSV
from .models import ElementWCS
from .models import ElementWFS
from .models import ElementWPS

from .models import WaterYieldModel

from .models import ServerElement
from .models import Job

from .forms import ServerFormCSV
from .forms import ServerFormWCS
from .forms import ServerFormWFS
from .forms import ServerFormWPS

from .forms import WaterYieldForm

from .forms import JobForm

from .forms import JobDynamic

import requests

import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString

import json
import html

import owslib.wps

from django.shortcuts import render_to_response
from django.template import RequestContext
from .forms import testForm

import django.core.exceptions

import copy
import collections

import bs4
import re

from os import sys, path
p = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(p)

import easyows
import uuid

import sys
import urllib
if sys.version_info.major == 2:
    quote = urllib.quote
    unquote = urllib.unquote
else:
    quote = urllib.parse.quote
    unquote = urllib.parse.unquote    
 
# Create your views here.
def dashboard(request):
    servers_csv = ServerCSV.objects.order_by('title')
    servers_wcs = ServerWCS.objects.order_by('title')
    servers_wfs = ServerWFS.objects.order_by('title')
    servers_wps = ServerWPS.objects.order_by('title')

    process_jobs = Job.objects.order_by('pk')
    
    return render(request, 'wpsclient/dashboard.html', {'servers_csv' : servers_csv,
                                                        'servers_wcs' : servers_wcs,
                                                        'servers_wfs' : servers_wfs,
                                                        'servers_wps' : servers_wps,                                                        
                                                        'process_list' : process_jobs})

def server_list(request, server_type):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS
        }

    ServerClass = server_dict[server_type]    
    servers = ServerClass.objects.order_by('title')
    return render(request, 'wpsclient/server_list.html', {'servers' : servers})

def server_detail(request, server_pk, server_type):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS
        }

    ServerClass = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)

    process_jobs = Job.objects.filter(server__pk=server_pk).order_by('pk')

    return render(request, 'wpsclient/server_detail.html', {'server': server,
                                                            'process_list' : process_jobs})

##def server_new(request, ows):
##    print(request.method, ows)
##    if request.method == "POST":
##        form = ServerForm(request.POST)
##        if form.is_valid():
##            server = form.save()
##            #server.save()
##            return redirect('server_detail', server_pk=server.pk)
##            
##    else: #elif request.method == "GET"
##        form = ServerForm()
##
##    return render(request, 'wpsclient/server_edit.html', {'form': form,
##                                                          'ows' : ows})

def server_register(request, server_type, title, url):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS
        }

    ServerClass = server_dict[server_type]

    server = ServerClass(title=title, url=url)
    server.save()

    return server_detail(request, server.pk, server_type)


def server_new(request, server_type):
    server_dict = {
        "CSV" : ServerFormCSV,
        "WCS" : ServerFormWCS,
        "WFS" : ServerFormWFS,
        "WPS" : ServerFormWPS
        }

    FormClass = server_dict[server_type]
    
    if request.method == "POST":
        form = FormClass(request.POST)
        if form.is_valid():
            server = form.save()
            #server.save()
            return redirect('server_detail', server_pk=server.pk, server_type=server.server_type)
            
    else: #elif request.method == "GET"
        form = FormClass()

    return render(request, 'wpsclient/server_edit.html', {'form': form,
                                                          'server_type' : server_type})

def server_csv_new(request):
    server_type = "CSV"
    server_new(request, server_type)

def server_wcs_new(request):
    server_type = "WCS"
    server_new(request, server_type)

def server_wfs_new(request):
    server_type = "WFS"
    server_new(request, server_type)

def server_wps_new(request):
    server_type = "WPS"
    server_new(request, server_type)


##def server_edit(request, server_pk):
##    server = get_object_or_404(ServerWPS, pk=server_pk)
##    if request.method == "POST":
##        form = ServerForm(request.POST, instance=server)
##        if form.is_valid():
##            server = form.save()
##            return redirect('server_detail', server_pk=server.pk)
##    else:
##        form = ServerForm(instance=server)
##    return render(request, 'wpsclient/server_edit.html', {'server' : server,
##                                                          'form': form})

def server_edit(request, server_pk, server_type):
    server_dict = {
        "CSV" : (ServerCSV, ServerFormCSV),
        "WCS" : (ServerWCS, ServerFormWCS),
        "WFS" : (ServerWFS, ServerFormWFS),
        "WPS" : (ServerWPS, ServerFormWPS)
        }

    ServerClass, FormClass = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)
    if request.method == "POST":
        form = FormClass(request.POST, instance=server)
        if form.is_valid():
            server = form.save()
            return redirect('server_detail', server_pk=server.pk, server_type=server.server_type)
    else:
        form = FormClass(instance=server)
    return render(request, 'wpsclient/server_edit.html', {'server' : server,
                                                          'form': form})

def server_csv_edit(request, server_pk):
    server_type = "CSV"
    return server_edit(request, server_pk, server_type)

def server_wcs_edit(request, server_pk):
    server_type = "WCS"
    return server_edit(request, server_pk, server_type)

def server_wfs_edit(request, server_pk):
    server_type = "WFS"
    return server_edit(request, server_pk, server_type)

def server_wps_edit(request, server_pk):
    server_type = "WPS"
    return server_edit(request, server_pk, server_type)

def get_csv_identifiers(server_url):
    html_page =requests.get(server_url).text
    soup = bs4.BeautifulSoup(html_page, features="html.parser")

    links = []
 
    for link in soup.findAll('a', attrs={'href': re.compile(".csv|.CSV|.zip|.ZIP$")}):
        links.append(link.get('href'))
 
    return links

def get_wcs_identifiers(server_url):
    link = server_url + "?service=wcs&version=1.0.0&request=GetCapabilities"
    capabilities = requests.get(link)

    tree = ET.fromstring(capabilities.text)
    identifiers = []
    for elem in tree.iter('{http://www.opengis.net/wcs}CoverageOfferingBrief'):
        identifiers.append(elem.find('{http://www.opengis.net/wcs}name').text)

    return identifiers

def get_wfs_identifiers(server_url):
    link = server_url + "?service=wfs&version=1.0.0&request=GetCapabilities"
    capabilities = requests.get(link)

    tree = ET.fromstring(capabilities.text)
    identifiers = []
    for elem in tree.iter('{http://www.opengis.net/wfs}FeatureType'):
        identifiers.append(elem.find('{http://www.opengis.net/wfs}Name').text)

    return identifiers

def get_wps_identifiers(server_url):
    link = server_url + "?service=wps&version=1.0.0&request=GetCapabilities"
    capabilities = requests.get(link)

    tree = ET.fromstring(capabilities.text)
    identifiers = []
    for elem in tree.iter('{http://www.opengis.net/wps/1.0.0}Process'):
        identifiers.append(elem.find('{http://www.opengis.net/ows/1.1}Identifier').text)

    return identifiers

def get_server_element_register_list(server_pk):
    return [element.identifier for element in ServerElement.objects.filter(server__pk=server_pk)]
    

def server_element_list(request, server_type, server_pk):
    server_dict = {
        "CSV" : (ServerCSV, get_csv_identifiers),
        "WCS" : (ServerWCS, get_wcs_identifiers),
        "WFS" : (ServerWFS, get_wfs_identifiers),        
        "WPS" : (ServerWPS, get_wps_identifiers)
        }

    ServerClass, get_list = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)
    server_elements = ServerElement.objects.filter(server__pk=server_pk)

    registered_element_list = get_server_element_register_list(server_pk)
    registered_element_list.sort()
    
    unregistered_element_list = []
    for identifier in get_list(server.url):
        if not (identifier in registered_element_list):
            unregistered_element_list.append(identifier)
    
    return render(request, 'wpsclient/server_element_list.html', {'server': server,
                                                                  'registered_element_list' : registered_element_list,
                                                                  'unregistered_element_list': unregistered_element_list})

def server_element_register(request, server_type, server_pk, element_id):
    server_dict = {
        "CSV" : (ServerCSV, ElementCSV), 
        "WCS" : (ServerWCS, ElementWCS),
        "WFS" : (ServerWFS, ElementWFS),
        "WPS" : (ServerWPS, ElementWPS)
        }

    ServerClass, ElementClass = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)

    element = ElementClass(server=server,identifier=element_id)
    element.save()

    server.registrations = server.registrations + 1
    server.save()

    return server_element_list(request, server_type, server_pk)

def server_element_unregister(request, server_type, server_pk, element_id):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS
        }

    ServerClass = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)

    element = ServerElement.objects.filter(server__pk=server_pk).filter(identifier=element_id).delete()

    server.registrations = server.registrations - 1
    server.save()

    return server_element_list(request, server_type, server_pk)

def server_element_detail(request, server_type, server_pk, element_id):
    server_dict = {
        "CSV" : server_csv_element_detail,        
        "WCS" : server_wcs_element_detail,
        "WFS" : server_wfs_element_detail,
        "WPS" : server_wps_element_detail
        }

    print(server_type)

    return server_dict[server_type](request, server_pk, element_id)

def server_csv_element_detail(request, server_pk, element_id):
    server = get_object_or_404(ServerCSV, pk=server_pk)

    link = server.url + '/' + element_id

    description = "No detail available."

    return render(request, 'wpsclient/text.html', {'text' : description})

def server_wcs_element_detail(request, server_pk, element_id):
    server = get_object_or_404(ServerWCS, pk=server_pk)
    link = server.url + "?service=WCS&version=1.0.0&request=DescribeCoverage&Coverage=" + element_id

    description = parseString(requests.get(link).text).toprettyxml()

    return render(request, 'wpsclient/text.html', {'text' : description})

def server_wfs_element_detail(request, server_pk, element_id):
    server = get_object_or_404(ServerWFS, pk=server_pk)
    link = server.url + "?service=WFS&version=1.0.0&request=DescribeFeatureType&typeName=" + element_id

    description = parseString(requests.get(link).text).toprettyxml()

    return render(request, 'wpsclient/text.html', {'text' : description})

def server_wps_element_detail(request, server_pk, element_id):
    server = get_object_or_404(ServerWPS, pk=server_pk)
    link = server.url + "?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=" + element_id
    description = parseString(requests.get(link).text).toprettyxml()

    wps = owslib.wps.WebProcessingService(server.url, verbose=False, skip_caps=True)
    process = wps.describeprocess(element_id)

    process_input = []
    for parameter in process.dataInputs:

        data_type = parameter.dataType
        if data_type == "ComplexData":
            data_type = "\n".join([m.mimeType for m in parameter.supportedValues])

        parameter_details = [parameter.identifier,
                             parameter.title,
                             parameter.abstract,
                             data_type,
                             parameter.minOccurs,
                             parameter.maxOccurs]

        parameter_details = [v if v != None else "" for v in parameter_details]
        process_input.append(parameter_details)

    process_output = []
    for parameter in process.processOutputs:

        data_type = parameter.dataType
        if data_type == "ComplexData":
            data_type = "\n".join([m.mimeType for m in parameter.supportedValues])

        parameter_details = [parameter.identifier,
                             parameter.title,
                             parameter.abstract,
                             data_type]

        parameter_details = [v if v != None else "" for v in parameter_details]
        process_output.append(parameter_details)
    
    
    return render(request, 'wpsclient/server_wps_describe_process.html', {'server': server,
                                                                      'process_id': element_id,
                                                                      'process_title' : process.title,
                                                                      'process_abstract' : process.abstract,
                                                                      'process_input' : process_input,
                                                                      'process_output' : process_output,
                                                                      'xml': description})    

def server_job_list(request, server_pk):
    process_jobs = Job.objects.filter(server__pk=server_pk).order_by('pk')
    return render(request, 'wpsclient/job_list.html', {'process_list' : process_jobs})


def job_list(request):
    process_jobs = Job.objects.order_by('pk')
    return render(request, 'wpsclient/job_list.html', {'process_list' : process_jobs})


def job_detail(request, job_pk):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])    
    #detail of an existing process with parameters
    job = get_object_or_404(Job, pk=job_pk)
    return render(request, 'wpsclient/job_detail.html', {'job': job})

##def job_new(request, server_pk, process_id):
##    server = get_object_or_404(ServerWPS, pk=server_pk)
##    link = server.url + "?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=" + process_id
##    description = requests.get(link)
##
##    if request.method == "POST":
##        form = ProcessForm(request.POST)
##        if form.is_valid():
##            process = form.save(commit=False)
##            process.server = server
##            process.identifier = process_id
##            process.save()
##
##            return redirect('job_detail', process_pk=process.pk)
##    else:
##        form = ProcessForm()
##
##    return render(request, 'wpsclient/job_edit.html', {'form': form,
##                                                           'server_title': server.title,
##                                                           'process_id': process_id})
##
##
##def job_edit(request, process_pk):
##    process = get_object_or_404(Job, pk=process_pk)
##    if request.method == "POST":
##        form = ProcessForm(request.POST, instance=process)
##        if form.is_valid():
##            form.save()
##            return redirect('job_detail', process_pk=process.pk)
##    else:
##        form = ProcessForm(instance=process)
##    return render(request, 'wpsclient/job_edit.html', {'form': form,
##                                                       'server_title' : process.server.title,
##                                                       'process_id' : process.identifier})

def get_wps_input_fields(server_pk, process_id):
    server = get_object_or_404(ServerWPS, pk=server_pk)

    wps = owslib.wps.WebProcessingService(server.url, verbose=False, skip_caps=True)
    process = wps.describeprocess(process_id)

    process_input = []
    for parameter in process.dataInputs:

        data_type = parameter.dataType
        if data_type == "ComplexData":
            data_type = "\n".join([m.mimeType for m in parameter.supportedValues])

        parameter_details = [parameter.identifier,
                             parameter.title,
                             parameter.abstract,
                             data_type,
                             parameter.minOccurs,
                             parameter.maxOccurs]

        parameter_details = [v if v != None else "" for v in parameter_details]
        process_input.append(parameter_details)

        return process_input

##def job_new_dynamic(request, server_pk, process_id):
##    l = logging.getLogger('django.request')
##    l.warning(inspect.stack()[0][3])
##    
##    server = get_object_or_404(ServerWPS, pk=server_pk)
##   
##    wps_input_fields = get_wps_input_fields(server_pk, process_id)
##    print([parameter[0] for parameter in wps_input_fields])
##
##    if request.method == "POST":
##        
##        form = JobDynamic(request.POST, wps_input_fields=wps_input_fields)      
##
##        args = collections.OrderedDict()
##        for (f, d) in form.wps_input_data():
##            print(f)
##            args[f] = d
##
##        process = Job(server=server,identifier=process_id,args=args)
##        process.save()
##
##        server.jobs = server.jobs + 1
##        server.save()
##            
##        return redirect('job_detail', process_pk=process.pk)
##
##    else:
##        form = JobDynamic(request.POST or None, wps_input_fields=wps_input_fields) 
##
##    return render_to_response("wpsclient/job_edit.html", {"form" : form})

def job_new_dynamic(request, server_pk, process_id, args):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])
    
    server = get_object_or_404(ServerWPS, pk=server_pk)

    args = json.loads(unquote(unquote(args)),
                      object_pairs_hook=collections.OrderedDict)
    #print(args)
    #print(request.method)

    if request.method == "GET":
        process = Job(server=server,identifier=process_id,args=args)
        process.status = "Validate"
        process.save()

        server.jobs = server.jobs + 1
        server.save()
        
        return redirect('job_detail', process_pk=process.pk)
    else:        
        pass
        
    return dashboard(request)

def job_validate(request, job_pk):

    job = get_object_or_404(Job, pk=job_pk)
    job.status = "Pending"
    job.save()

    return dashboard(request)

  
def job_new(request, server_pk, process_id):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])
    
    server = get_object_or_404(ServerWPS, pk=server_pk)
    #link = server.url + "?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=" + process_id
    #description = requests.get(link)

    args = collections.OrderedDict()

    wps = owslib.wps.WebProcessingService(server.url, verbose=False, skip_caps=True)
    process = wps.describeprocess(process_id)

    for parameter in process.dataInputs:            
        if parameter.dataType == "double":
            args[parameter.identifier] = float(0)
        elif parameter.dataType == "int":
            args[parameter.identifier] = int(0)                
        else:
            args[parameter.identifier] = ""

    if request.method == "POST":
        form = testForm(request.POST)

##        l.warning(str(dir(form)))
##        l.warning(str(form.data))
        data = copy.copy(form.data)
        del data["csrfmiddlewaretoken"]
        keys=list(data.keys())
        key_values = []
        strip_index=len("data__")
        for k in keys:
            key_values.append((k[strip_index:], type(args[k[strip_index:]])(data[k])))
        
        #form.data.pop('QueryDict')

##        l.warning(str(list(request.POST.keys())))
##        keys = list(request.POST.keys())
##        keys.pop(0)
##        values = json()
##        for k in keys:
##            json[

        #form.data["csrfmiddlewaretoken"].delete()
            
        args= collections.OrderedDict(key_values)
        job = Job(server=server,identifier=process_id,args=args)

        job.status = "Run"
        status_url = server.url + "?service=wps&version=1.0.0&request=Execute&IDENTIFIER=" + job.identifier + "&datainputs="
        status_url = status_url + ";".join(["%s=%s" % (k, quote(quote(job.args[k]))) for k in job.args.keys()])
        job.status_url = status_url
        
        job.save()

        server.jobs = server.jobs + 1
        server.save()
        
        return redirect('job_detail', job_pk=job.pk)
    else:        
        form = testForm(request.POST or None, initial={'data': args})
        
    return render(request, 'wpsclient/job_edit.html', {'form': form})

def job_edit(request, job_pk):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])
    
    job = get_object_or_404(Job, pk=job_pk)

    if request.method == "POST":
        form = testForm(request.POST)        
##        l.warning(str(dir(form)))
##        l.warning(str(form.data))

        #form.data["csrfmiddlewaretoken"].delete()        

        keys = list(form.data.keys())
        keys.remove("csrfmiddlewaretoken")
        key_values = []
        for k in keys:
            #get values and preserve data types
            key_values.append((k[6:], type(job.args[k[6:]])(form.data[k])))
        
        #form.data.pop('QueryDict')

##        l.warning(str(list(request.POST.keys())))
##        keys = list(request.POST.keys())
##        keys.pop(0)
##        values = json()
##        for k in keys:
##            json[

        #l.warning(key_values)
        job.args= collections.OrderedDict(key_values)
        job.save()
        return redirect('job_detail', job_pk=job.pk)

    else:
        form = testForm(request.POST or None, initial={'data': job.args})

    return render(request, 'wpsclient/job_edit.html', {"server_title" : job.server.title,
                                                       "process_id" : job.identifier,
                                                       'form': form})

def get_server_element(pk):
    element_types = [ElementCSV,
                     ElementWCS,
                     ElementWFS,
                     ElementWPS]

    for e_type in element_types:
        try:
            return e_type.objects.get(pk=pk)
        except django.core.exceptions.ObjectDoesNotExist:
            pass

    return None
            
def get_ows_data_url(server_type, server_url, identifier):
    ows_templates = {
        "CSV" : "%s/%s",
        "WCS" : "%s/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=%s&format=image%%2Fgeotiff",
        "WFS" : "%s/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=SHAPE-ZIP",
        }

    return ows_templates[server_type] % (server_url, identifier)
 
def water_yield(request):
    if request.method == "POST":
        form = WaterYieldForm(request.POST)

        #clean up data and convert server element ids to gettable URLs
        data = copy.copy(form.data)
        del data["csrfmiddlewaretoken"]

        keys = set(data.keys())
        keys.remove("seasonality_constant")

        for k in keys:
            element = get_server_element(data[k])
            data[k] = get_ows_data_url(element.element_type,element.server.url,element.identifier)      

        #save data to a job and redirect to details
        args = data
        server_pk="4"
        server = get_object_or_404(ServerWPS, pk=server_pk)
        process_id="natcap.invest.hydropower.hydropower_water_yield"

        #cat = easyows.Catalog()
        name = str(uuid.uuid1())
        #cat.gs_cat.create_workspace(name)
        args["workspace_dir"] = name
        
        job = Job(server=server,identifier=process_id,args=args)

        job.status = "Run"
        status_url = server.url + "?service=wps&version=1.0.0&request=Execute&IDENTIFIER=natcap.invest.hydropower.hydropower_water_yield&datainputs="
        status_url = status_url + ";".join(["%s=%s" % (k, quote(quote(job.args[k]))) for k in job.args.keys()])
        job.status_url = status_url
        
        job.save()               

        server.jobs = server.jobs + 1
        server.save()
        
        return redirect('job_detail', job_pk=job.pk)        
            
    else: #elif request.method == "GET"
        form = WaterYieldForm()

    return render(request, 'wpsclient/water_yield.html', {'form': form})

def job_run(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)

    if job.status = "Validate":
        job.status = "Run"
        job.save()

        return dashboard(request)    

    elif job.status = "Run":
        msg = job.status_url
        return render(request, "wpsclient/job_run.html", {"msg" : msg})


    
