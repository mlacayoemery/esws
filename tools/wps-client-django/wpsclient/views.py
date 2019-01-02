import logging
import inspect

from django.shortcuts import render, get_object_or_404, redirect

from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS

from .models import ProcessWPS

from .forms import ServerFormCSV
from .forms import ServerFormWCS
from .forms import ServerFormWFS
from .forms import ServerFormWPS

from .forms import ProcessWPSForm

from .models import ServerWCS
from .forms import ServerFormWCS
import requests

import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString

import json
import html

import owslib.wps

from django.shortcuts import render_to_response
from django.template import RequestContext
from .forms import testForm

import collections

# Create your views here.
def dashboard(request):
    servers_csv = ServerCSV.objects.order_by('title')
    servers_wcs = ServerWCS.objects.order_by('title')
    servers_wfs = ServerWFS.objects.order_by('title')
    servers_wps = ServerWPS.objects.order_by('title')

    process_jobs = ProcessWPS.objects.order_by('pk')
    
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

    process_jobs = ProcessWPS.objects.filter(server__pk=server_pk).order_by('pk')

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
    server_edit(request, server_pk, server_type)

def server_wcs_edit(request, server_pk):
    server_type = "WCS"
    server_edit(request, server_pk, server_type)

def server_wfs_edit(request, server_pk):
    server_type = "WFS"
    server_edit(request, server_pk, server_type)

def server_wps_edit(request, server_pk):
    server_type = "WPS"
    server_edit(request, server_pk, server_type)


def server_wps_capabilities(request, server_type, server_pk):
    server = get_object_or_404(ServerWPS, pk=server_pk)
    link = server.url + "?service=wps&version=1.0.0&request=GetCapabilities"
    capabilities = requests.get(link)

    tree = ET.fromstring(capabilities.text)
    processes = []
    for elem in tree.iter('{http://www.opengis.net/wps/1.0.0}Process'):
        processes.append(elem.find('{http://www.opengis.net/ows/1.1}Identifier').text)
    
    return render(request, 'wpsclient/server_wps_capabilities.html', {'server': server,
                                                                  'processes': processes})    

def server_wps_describe_process(request, server_type, server_pk, process_id):
    server = get_object_or_404(ServerWPS, pk=server_pk)
    link = server.url + "?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=" + process_id
    description = parseString(requests.get(link).text).toprettyxml()

    wps = owslib.wps.WebProcessingService(server.url, verbose=False, skip_caps=True)
    process = wps.describeprocess(process_id)

    process_input = []
    for parameter in process.dataInputs:

        parameter_details = [parameter.identifier,
                             parameter.title,
                             parameter.abstract,
                             parameter.dataType,
                             parameter.minOccurs,
                             parameter.maxOccurs]

        parameter_details = [v if v != None else "" for v in parameter_details]
        process_input.append(parameter_details)

    process_output = []
    for parameter in process.processOutputs:

        parameter_details = [parameter.identifier,
                             parameter.title,
                             parameter.abstract,
                             parameter.dataType]

        parameter_details = [v if v != None else "" for v in parameter_details]
        process_output.append(parameter_details)
    
    
    return render(request, 'wpsclient/server_wps_describe_process.html', {'server': server,
                                                                      'process_id': process_id,
                                                                      'process_title' : process.title,
                                                                      'process_abstract' : process.abstract,
                                                                      'process_input' : process_input,
                                                                      'process_output' : process_output,
                                                                      'xml': description})    

def server_job_list(request, server_pk):
    process_jobs = ProcessWPS.objects.filter(server__pk=server_pk).order_by('pk')
    return render(request, 'wpsclient/job_list.html', {'process_list' : process_jobs})


def job_list(request):
    process_jobs = ProcessWPS.objects.order_by('pk')
    return render(request, 'wpsclient/job_list.html', {'process_list' : process_jobs})


def job_detail(request, process_pk):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])    
    #detail of an existing process with parameters
    process = get_object_or_404(ProcessWPS, pk=process_pk)
    return render(request, 'wpsclient/job_detail.html', {'process': process})

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
##    process = get_object_or_404(ProcessWPS, pk=process_pk)
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
        keys=list(form.data.keys())
        keys.pop(0)
        key_values = []
        for k in keys:
            key_values.append((k[6:], type(args[k[6:]])(form.data[k])))
        
        #form.data.pop('QueryDict')

##        l.warning(str(list(request.POST.keys())))
##        keys = list(request.POST.keys())
##        keys.pop(0)
##        values = json()
##        for k in keys:
##            json[

        #form.data["csrfmiddlewaretoken"].delete()
            
        args= collections.OrderedDict(key_values)
        process = ProcessWPS(server=server,identifier=process_id,args=args)
        process.save()
        
        return redirect('job_detail', process_pk=process.pk)
    else:        
        form = testForm(request.POST or None, initial={'data': args})
        
    return render(request, 'wpsclient/job_edit.html', {'form': form})

def job_edit(request, process_pk):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])
    
    process = get_object_or_404(ProcessWPS, pk=process_pk)

    if request.method == "POST":
        form = testForm(request.POST)        
##        l.warning(str(dir(form)))
##        l.warning(str(form.data))
        keys=list(form.data.keys())
        keys.pop(0)
        key_values = []
        for k in keys:
            #get values and preserve data types
            key_values.append((k[6:], type(process.args[k[6:]])(form.data[k])))
        
        #form.data.pop('QueryDict')

##        l.warning(str(list(request.POST.keys())))
##        keys = list(request.POST.keys())
##        keys.pop(0)
##        values = json()
##        for k in keys:
##            json[

        #form.data["csrfmiddlewaretoken"].delete()
        #l.warning(key_values)
        process.args= collections.OrderedDict(key_values)
        process.save()
        return redirect('job_detail', process_pk=process.pk)

    else:
        form = testForm(request.POST or None, initial={'data': process.args})

    return render(request, 'wpsclient/job_edit.html', {'form': form})
