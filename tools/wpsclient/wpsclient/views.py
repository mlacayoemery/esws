import logging
import inspect

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponse
from django.utils import timezone

from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS
from .models import ServerTemplate

from .models import ElementCSV
from .models import ElementWCS
from .models import ElementWFS
from .models import ElementWPS


from .models import ServerElement
from .models import Job
from .models import ElementFingerprint
from .models import ElementProvenance

from .forms import ServerFormCSV
from .forms import ServerFormWCS
from .forms import ServerFormWFS
from .forms import ServerFormWPS
from .forms import ServerFormTemplate

from .forms import ProcessForm
from .forms import UNIQUE_RUN_FIELD
from .forms import REACTIVE_FIELD

from .forms import JobForm

from .forms import JobDynamic

import requests

import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString

import json
import html

import owslib.wps

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
    urlretrieve = urllib.URLopener().retrieve
else:
    quote = urllib.parse.quote
    unquote = urllib.parse.unquote
    from urllib.request import urlretrieve
 
# Create your views here.
def dashboard(request):
    servers_csv = ServerCSV.objects.order_by('title')
    servers_wcs = ServerWCS.objects.order_by('title')
    servers_wfs = ServerWFS.objects.order_by('title')
    # A template is also a ServerWPS, so keep it out of the WPS list.
    servers_wps = ServerWPS.objects.filter(servertemplate__isnull=True).order_by('title')
    servers_tpl = ServerTemplate.objects.order_by('title')

    process_jobs = Job.objects.order_by('pk')
    
    return render(request, 'wpsclient/dashboard.html', {'servers_csv' : servers_csv,
                                                        'servers_wcs' : servers_wcs,
                                                        'servers_wfs' : servers_wfs,
                                                        'servers_wps' : servers_wps,
                                                        'servers_tpl' : servers_tpl,
                                                        'process_list' : process_jobs})

def server_list(request, server_type):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS,
        "TPL" : ServerTemplate
        }

    ServerClass = server_dict[server_type]
    servers = ServerClass.objects.order_by('title')
    if server_type == "WPS":
        servers = servers.filter(servertemplate__isnull=True)
    return render(request, 'wpsclient/server_list.html',
                  {'servers' : servers, 'server_type' : server_type})

def server_detail(request, server_pk, server_type):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS,
        "TPL" : ServerTemplate
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
        "WPS" : ServerWPS,
        "TPL" : ServerTemplate
        }

    ServerClass = server_dict[server_type]

    # Keyed on title *and* URL so re-registering updates rather than
    # duplicating -- the demo loader is meant to be safe to re-run. URL alone is
    # not unique: a template shares its WPS's URL, and since ServerTemplate
    # subclasses ServerWPS both satisfy a ServerWPS lookup, so keying on the URL
    # matched two rows and raised MultipleObjectsReturned on the second run.
    candidates = ServerClass.objects.filter(url=url, title=title)
    if server_type == "WPS":
        candidates = candidates.filter(servertemplate__isnull=True)

    server = candidates.first()
    if server is None:
        server = ServerClass(title=title, url=url)
        server.save()

    return server_detail(request, server.pk, server_type)


def server_new(request, server_type):
    server_dict = {
        "CSV" : ServerFormCSV,
        "WCS" : ServerFormWCS,
        "WFS" : ServerFormWFS,
        "WPS" : ServerFormWPS,
        "TPL" : ServerFormTemplate
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
        "WPS" : (ServerWPS, ServerFormWPS),
        "TPL" : (ServerTemplate, ServerFormTemplate)
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
        "WPS" : (ServerWPS, get_wps_identifiers),
        # A template lists the same processes as the WPS it points at.
        "TPL" : (ServerTemplate, get_wps_identifiers)
        }

    ServerClass, get_list = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)
    server_elements = ServerElement.objects.filter(server__pk=server_pk)

    registered_element_list = get_server_element_register_list(server_pk)
    registered_element_list.sort()
    
    unregistered_element_list = []
    # A "Local Pending" source is a holding area, not a live endpoint: it lists
    # what a running job is expected to produce. Asking it for its contents the
    # usual way means contacting a URL that does not resolve, which 500s the
    # page -- so only the registered entries are shown.
    if not server.is_pending:
        for identifier in get_list(server.url):
            if not (identifier in registered_element_list):
                unregistered_element_list.append(identifier)
    
    # Fingerprints for the bookmarked elements, so the list can show when each was
    # last checked and last seen to change. Only data sources have them.
    checkable = server_type in _CHECKABLE
    recorded = {}
    if checkable:
        recorded = {f.element.identifier: f for f in
                    ElementFingerprint.objects.filter(
                        element__server__pk=server_pk).select_related("element")}
    registered_rows = [(identifier, recorded.get(identifier))
                       for identifier in registered_element_list]

    return render(request, 'wpsclient/server_element_list.html', {'server': server,
                                                                  'registered_element_list' : registered_element_list,
                                                                  'registered_rows' : registered_rows,
                                                                  'checkable' : checkable,
                                                                  'unregistered_element_list': unregistered_element_list})

def server_element_register(request, server_type, server_pk, element_id):
    server_dict = {
        "CSV" : (ServerCSV, ElementCSV), 
        "WCS" : (ServerWCS, ElementWCS),
        "WFS" : (ServerWFS, ElementWFS),
        "WPS" : (ServerWPS, ElementWPS),
        "TPL" : (ServerTemplate, ElementWPS)
        }

    ServerClass, ElementClass = server_dict[server_type]
    
    server = get_object_or_404(ServerClass, pk=server_pk)

    # Same reasoning as server_register: registering an element twice should
    # be a no-op, not a duplicate row in every dropdown.
    element, _created = ElementClass.objects.get_or_create(
        server=server, identifier=element_id)

    server.registrations = server.registrations + 1
    server.save()

    return server_element_list(request, server_type, server_pk)

def server_element_unregister(request, server_type, server_pk, element_id):
    server_dict = {
        "CSV" : ServerCSV,
        "WCS" : ServerWCS,
        "WFS" : ServerWFS,
        "WPS" : ServerWPS,
        "TPL" : ServerTemplate
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
        "WPS" : server_wps_element_detail,
        # A template describes its processes exactly like the WPS it points at.
        "TPL" : server_wps_element_detail
        }

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

    wps = owslib.wps.WebProcessingService(server.url, skip_caps=True)
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
    
    
    # ows:Metadata the process declares -- its licences and its user guide. owslib
    # names the link `url`, not `href`.
    process_metadata = [(m.title, m.url, (m.role or "").rsplit(":", 1)[-1])
                        for m in getattr(process, "metadata", None) or []]

    return render(request, 'wpsclient/server_wps_describe_process.html', {'server': server,
                                                                      'process_id': element_id,
                                                                      'process_title' : process.title,
                                                                      'process_abstract' : process.abstract,
                                                                      'process_metadata' : process_metadata,
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
    return render(request, 'wpsclient/job_detail.html',
                  {'job': job,
                   # Only a finished job is worth resubmitting; while it is still
                   # running, job_run is the poll.
                   'can_rerun': job.status in _JOB_FINISHED,
                   'unique_run': wants_unique_run(job),
                   'reactive': wants_reaction(job)})

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

    wps = owslib.wps.WebProcessingService(server.url, skip_caps=True)
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
        job = Job(server=server,identifier=process_id,args=args)
        job.status = "Validate"
        job.save()

        server.jobs = server.jobs + 1
        server.save()
        
        return redirect('job_detail', job_pk=job.pk)
    else:        
        pass
        
    return dashboard(request)

def job_validate(request, job_pk):

    job = get_object_or_404(Job, pk=job_pk)
    job.status = "Pending"
    job.save()

    return dashboard(request)

  
# Output kind -> (pending server title, server class, element class)
PENDING_SOURCES = {
    "raster": ("Local Pending WCS", ServerWCS, ElementWCS),
    "vector": ("Local Pending WFS", ServerWFS, ElementWFS),
    "table": ("Local Pending HTTP", ServerCSV, ElementCSV),
}


def pending_server(kind):
    """The holding source for a kind of anticipated output, created on demand."""
    entry = PENDING_SOURCES.get(kind)
    if entry is None:
        return None, None
    title, ServerClass, ElementClass = entry
    server, _created = ServerClass.objects.get_or_create(
        title=title, defaults={"url": "http://pending.invalid/%s" % kind,
                               "is_pending": True})
    if not server.is_pending:
        server.is_pending = True
        server.save()
    return server, ElementClass


def anticipated_for_job(job):
    """[(kind, name)] this job is expected to produce.

    Computed from MODEL_SPEC the same way the WPS computes what to publish --
    created_if evaluated against the job's own arguments, and results_suffix
    applied -- so the pending list matches what actually turns up.
    """
    scripts = "/app/tools"
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        from invest_outputs import resolved_output_paths
        from natcap.invest import models as invest_models_registry
    except Exception:  # noqa: BLE001 - not an InVEST server: nothing to predict
        return []

    spec = invest_models_registry.model_id_to_spec.get(job.identifier)
    if spec is None:
        return []

    # Only the argument values matter for created_if and the suffix, so the
    # workspace is irrelevant here; names are taken from the resolved basenames.
    out = []
    for output, resolved in resolved_output_paths(spec, "/anticipated",
                                                 effective_args(job),
                                                 primary_only=True):
        lower = resolved.lower()
        if lower.endswith((".tif", ".tiff")):
            kind = "raster"
        elif lower.endswith((".shp", ".gpkg")):
            kind = "vector"
        elif lower.endswith(".csv"):
            kind = "table"
        else:
            continue
        name = path.basename(resolved)
        if kind != "table":
            name = path.splitext(name)[0]
        out.append((kind, name))
    return out


def register_pending(job):
    """List a job's anticipated outputs under the Local Pending sources."""
    if not any(job.args.get(field) for field in
               ("destination_wcs", "destination_wfs", "destination_http")):
        return 0

    added = 0
    for kind, name in anticipated_for_job(job):
        server, ElementClass = pending_server(kind)
        if server is None:
            continue
        # Scoped by job: two runs of one model anticipate identical names, and a
        # failed run's entries stay listed under its own job id.
        identifier = "job%s:%s" % (job.pk, name)
        _element, created = ElementClass.objects.get_or_create(
            server=server, identifier=identifier)
        added += int(created)
    return added


def clear_pending(job):
    """Drop this job's pending entries once its outputs are real."""
    removed = 0
    prefix = "job%s:" % job.pk
    for _title, _ServerClass, ElementClass in PENDING_SOURCES.values():
        removed += ElementClass.objects.filter(
            server__is_pending=True, identifier__startswith=prefix).delete()[0]
    return removed


def reconcile_uploads(job, xml):
    """Turn a finished job's anticipated outputs into registered ones.

    The WPS reports what it published in its `uploaded` output -- entries of
    <kind>:<workspace>:<name>, or table:<filename> -- so the client reconciles
    from the response instead of the server calling back into it.
    """
    match = re.search(r"uploaded</ows:Identifier>.*?<wps:LiteralData[^>]*>"
                      r"([^<]*)</wps:LiteralData>", xml, re.S)
    if not match:
        return 0
    entries = [e for e in match.group(1).strip().split(";") if e]

    registered = 0
    for entry in entries:
        bits = entry.split(":")
        kind = bits[0]
        identifier = ":".join(bits[1:])
        if not identifier:
            continue

        destination_url = job.args.get(
            {"raster": "destination_wcs", "vector": "destination_wfs",
             "table": "destination_http"}.get(kind, ""))
        if not destination_url:
            continue

        entry_map = PENDING_SOURCES.get(kind)
        if entry_map is None:
            continue
        _title, ServerClass, ElementClass = entry_map
        server = ServerClass.objects.filter(url=destination_url,
                                            is_pending=False).first()
        if server is None:
            continue

        element, created = ElementClass.objects.get_or_create(
            server=server, identifier=identifier)
        registered += int(created)

        # Remember what made it, so the pipeline the jobs form can be drawn.
        ElementProvenance.objects.update_or_create(
            element=element.serverelement_ptr, defaults={"job": job})

    if entries:
        clear_pending(job)
    return registered


def template_initial(process_id):
    """Initial form values for a template source: InVEST's own sample arguments.

    The sample archives ship datastacks -- complete, known-good arg sets per
    model -- so the defaults are InVEST's rather than invented. File arguments
    are matched back to the elements scripts/load_demo.py registered, using the
    same layer naming it published under, so the dropdowns come *preselected*
    instead of merely filled with a path.

    Returns {} if the sample cache is not mounted or the model has no
    datastack, in which case the form renders empty as usual.
    """
    scripts_dir = "/app/scripts"
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        import invest_sample_manifest as manifest
        import load_demo
    except Exception:  # noqa: BLE001 - no sample cache: fall back to empty form
        return {}

    # The manifest defaults to the host cache path; inside a container the
    # samples are mounted elsewhere, so point it at the same root load_demo
    # publishes from.
    manifest.SAMPLES = load_demo.SAMPLES

    try:
        entries, _unmatched = manifest.build()
    except Exception:  # noqa: BLE001
        return {}

    entry = entries.get(process_id)
    if not entry or not entry.get("datastacks"):
        return {}
    stack = entry["datastacks"][0]

    element_for_ext = {
        ".tif": ElementWCS, ".tiff": ElementWCS,
        ".shp": ElementWFS, ".gpkg": ElementWFS,
        ".csv": ElementCSV,
    }

    initial = {}
    for key, value in stack["args"].items():
        if key in ("workspace_dir", "n_workers"):
            continue
        if not isinstance(value, str):
            initial[key] = value
            continue

        candidate = value
        if not path.isabs(candidate):
            candidate = path.join(stack["dir"], candidate)
        if not path.exists(candidate):
            initial[key] = value
            continue

        resolved = path.realpath(candidate)
        ext = path.splitext(resolved)[1].lower()
        ElementClass = element_for_ext.get(ext)
        if ElementClass is None:
            initial[key] = value
            continue

        if ext == ".csv":
            identifier = "invest/%s" % path.relpath(resolved, load_demo.SAMPLES)
        else:
            identifier = "%s:%s" % (load_demo.WORKSPACE,
                                    load_demo.layer_name(resolved))

        element = ElementClass.objects.filter(identifier=identifier).first()
        # A ModelChoiceField takes the primary key; fall back to the raw value
        # so an unpublished input still shows something meaningful.
        initial[key] = element.pk if element else value

    return initial



def job_new(request, server_pk, process_id):
    l = logging.getLogger('django.request')
    l.warning(inspect.stack()[0][3])
    
    server = get_object_or_404(ServerWPS, pk=server_pk)
    #link = server.url + "?service=wps&version=1.0.0&request=DescribeProcess&IDENTIFIER=" + process_id
    #description = requests.get(link)

    wps = owslib.wps.WebProcessingService(server.url, skip_caps=True)
    process = wps.describeprocess(process_id)
    parameters = process.dataInputs
    is_template = ServerTemplate.objects.filter(pk=server_pk).exists()

    if request.method == "POST":
        form = ProcessForm(request.POST, parameters=parameters)
        if form.is_valid():
            args = collections.OrderedDict()
            for name, value in form.cleaned_data.items():
                if name == REACTIVE_FIELD:
                    if value:
                        args[REACTIVE_OPTION] = "true"
                    continue
                if name == UNIQUE_RUN_FIELD:
                    # Ours, not the WPS's: recorded under its namespaced key so
                    # effective_args keeps it out of the Execute request.
                    if value:
                        args[UNIQUE_RUN_OPTION] = "true"
                    continue
                if value is None or value == "":
                    continue
                if name in getattr(form, "destination_fields", {}):
                    # The WPS wants the endpoint, not our row id.
                    value = value.url
                elif name in form.element_fields:
                    # A chosen data source becomes the URL the WPS will fetch,
                    # the same conversion the water yield form used to do.
                    value = get_ows_data_url(value.element_type,
                                             value.server.url,
                                             value.identifier)
                elif isinstance(value, bool):
                    value = "true" if value else "false"
                args[name] = str(value)

            job = Job(server=server, identifier=process_id, args=args)
            job.status = "Run"
            status_url = (server.url +
                          "?service=wps&version=1.0.0&request=Execute&IDENTIFIER=" +
                          job.identifier + "&datainputs=")
            status_url += ";".join("%s=%s" % (k, quote(quote(v)))
                                   for k, v in args.items())
            job.status_url = status_url
            job.save()

            server.jobs = server.jobs + 1
            server.save()

            return redirect('job_detail', job_pk=job.pk)
    else:
        initial = template_initial(process_id) if is_template else None
        form = ProcessForm(parameters=parameters, initial=initial)

    return render(request, 'wpsclient/job_edit.html',
                  {'form': form,
                   'server_title': server.title,
                   'process_id': process_id,
                   'is_template': is_template})

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
 
# Element kinds whose data can be fetched and so fingerprinted. A WPS process is
# not data: there is nothing to hash.
_CHECKABLE = {"CSV": ServerCSV, "WCS": ServerWCS, "WFS": ServerWFS}


def check_element(element, kind):
    """Fingerprint one element's data, recording whether it changed.

    Returns "changed", "unchanged", or "unreachable". The three are distinct on
    purpose: a source that cannot be reached is not a source that is the same.
    """
    tools = "/app/tools"
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from data_fingerprint import fingerprint

    url = get_ows_data_url(kind, element.server.url, element.identifier)

    record, _created = ElementFingerprint.objects.get_or_create(element=element)
    previous = {"digest": record.digest, "etag": record.etag,
                "last_modified": record.last_modified, "size": record.size}

    result = fingerprint(url, previous=previous if record.digest else None)

    record.checks += 1
    record.checked_at = timezone.now()
    if not result["digest"]:
        record.unreachable = True
        record.save()
        return "unreachable"

    record.unreachable = False
    changed = bool(record.digest) and record.digest != result["digest"]
    if changed:
        record.changed_at = record.checked_at
    record.digest = result["digest"]
    record.etag = result["etag"] or ""
    record.last_modified = result["last_modified"] or ""
    record.size = result["size"]
    record.save()
    return "changed" if changed else "unchanged"


def server_check(request, server_type, server_pk):
    """Fingerprint every element bookmarked on a server.

    Note that this fetches the data: a source offering neither ETag nor
    Last-Modified -- which is every OWS response GeoServer generates -- has to be
    downloaded to be hashed.
    """
    ServerClass = _CHECKABLE.get(server_type)
    if ServerClass is None:
        raise Http404("%s elements are not data" % server_type)

    server = get_object_or_404(ServerClass, pk=server_pk)
    tally = {"changed": [], "unchanged": [], "unreachable": []}
    for element in ServerElement.objects.filter(server__pk=server_pk):
        try:
            tally[check_element(element, server_type)].append(element.identifier)
        except Exception as exc:  # noqa: BLE001 - one bad element must not stop the sweep
            l.warning("Could not check %s: %s", element.identifier, exc)
            tally["unreachable"].append(element.identifier)

    return render(request, "wpsclient/server_check.html",
                  {"server": server, "server_type": server_type, "tally": tally})


def water_yield(request):
    """Redirect to the generated form for the annual water yield model.

    This used to be a hand-built form: a fixed set of fields, each a dropdown
    of registered data sources, wired to a WaterYieldModel whose ForeignKeys
    hardcoded which element type every input wanted -- and to server_pk="4".
    ProcessForm now derives exactly that from DescribeProcess for any process,
    so the bespoke page, form and model are gone and this only redirects.
    """
    server = ServerWPS.objects.order_by("pk").first()
    if server is None:
        return redirect("server_list", server_type="WPS")
    return redirect("job_new", server_pk=server.pk,
                    process_id="annual_water_yield")


# Client-side job options live in job.args under this prefix. They are the
# dashboard's own settings, not WPS inputs, and are stripped before submission --
# kept in args because the wpsclient app has migrations disabled
# (MIGRATION_MODULES) and so cannot gain a column without recreating the table.
_OPTION_PREFIX = "esws:"
UNIQUE_RUN_OPTION = _OPTION_PREFIX + "unique_run"
RUN_TOKEN_OPTION = _OPTION_PREFIX + "run_token"
REACTIVE_OPTION = _OPTION_PREFIX + "reactive"
LAST_RUN_OPTION = _OPTION_PREFIX + "last_run"


def wants_unique_run(job):
    return str(job.args.get(UNIQUE_RUN_OPTION, "")).lower() in ("true", "1", "yes")


def rotate_run_token(job):
    """Give this run its own results_suffix, so an earlier run's outputs survive.

    Output filenames -- and therefore the layer names they are published under --
    come from results_suffix, so without a per-run token a second run overwrites
    the first. Eight hex digits is enough to keep runs apart while leaving the
    names readable.
    """
    if not wants_unique_run(job):
        return
    job.args[RUN_TOKEN_OPTION] = uuid.uuid4().hex[:8]


def wants_reaction(job):
    return str(job.args.get(REACTIVE_OPTION, "")).lower() in ("true", "1", "yes")


def job_input_elements(job):
    """The registered elements a job's arguments point at.

    Matched by rebuilding each element's data URL and comparing: the job stores
    the URL it will hand the WPS, not the row it was chosen from, because that is
    what the WPS needs.
    """
    wanted = {str(value) for value in job.args.values() if str(value).startswith("http")}
    if not wanted:
        return []

    matched = []
    for server_type, ServerClass in _CHECKABLE.items():
        for element in ServerElement.objects.filter(
                server__in=ServerClass.objects.filter(is_pending=False)):
            url = get_ows_data_url(server_type, element.server.url,
                                   element.identifier)
            if url in wanted:
                matched.append((element, server_type))
    return matched


def react_to_changes(job):
    """Re-run ``job`` if any of its inputs changed since it last ran.

    Returns (action, changed identifiers). Checking is the point: a job cannot
    react to a change nobody has looked for, so this fingerprints the inputs
    itself rather than trusting whenever they were last checked.
    """
    inputs = job_input_elements(job)
    if not inputs:
        return "no inputs", []

    last_run = job.args.get(LAST_RUN_OPTION) or ""
    changed = []
    for element, server_type in inputs:
        state = check_element(element, server_type)
        if state != "changed":
            continue
        record = ElementFingerprint.objects.filter(element=element).first()
        # Only a change since the job ran is a reason to run it again.
        if record and record.changed_at and (
                not last_run or record.changed_at.isoformat() > last_run):
            changed.append(element.identifier)

    if not changed:
        return "unchanged", []

    job.status = "Run"
    job.status_location = ""
    rotate_run_token(job)
    job.save()
    return "rerun", changed


def _pipeline():
    """The job pipeline as (nodes, edges), derived from what jobs consume and
    produce. Nothing declares it -- see tools/job_graph.py."""
    tools = "/app/tools"
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import job_graph

    produced_by = {}
    for record in ElementProvenance.objects.select_related("element"):
        produced_by[record.element.identifier] = record.job_id

    jobs = list(Job.objects.order_by("pk"))
    inputs_of = {}
    for job in jobs:
        inputs_of[job.pk] = [element.identifier
                             for element, _kind in job_input_elements(job)]
    return job_graph, job_graph.build(jobs, produced_by, inputs_of)


def job_graph_view(request):
    """The pipeline the jobs form, drawn."""
    module, (nodes, edges) = _pipeline()
    return render(request, "wpsclient/job_graph.html",
                  {"diagram": module.to_mermaid(nodes, edges),
                   "job_count": len(nodes), "edge_count": len(edges)})


def job_graph_bpmn(request):
    """The same pipeline as BPMN 2.0, for a modeller such as bpmn.io."""
    module, (nodes, edges) = _pipeline()
    response = HttpResponse(module.to_bpmn(nodes, edges),
                            content_type="application/xml")
    response["Content-Disposition"] = 'attachment; filename="esws-pipeline.bpmn"'
    return response


def job_react(request, job_pk):
    """Check one job's inputs and re-run it if they changed."""
    job = get_object_or_404(Job, pk=job_pk)
    action, changed = react_to_changes(job)
    if action == "rerun":
        return redirect("job_run", job_pk=job.pk)
    return render(request, "wpsclient/job_react.html",
                  {"jobs": [(job, action, changed)]})


def job_react_all(request):
    """Check every job that asked to react, and re-run those whose inputs changed.

    Re-runs are submitted here rather than redirected to, since there may be more
    than one. Meant to be reachable from cron as well as from the page.
    """
    results = []
    for job in Job.objects.order_by("pk"):
        if not wants_reaction(job):
            continue
        action, changed = react_to_changes(job)
        if action == "rerun":
            try:
                job_run(request, job.pk)
            except Exception as exc:  # noqa: BLE001 - report the rest regardless
                l.warning("Could not resubmit job %s: %s", job.pk, exc)
                action = "rerun failed: %s" % str(exc)[:80]
        results.append((job, action, changed))
    return render(request, "wpsclient/job_react.html", {"jobs": results})


def effective_args(job):
    """The WPS inputs for this run: job.args minus our options, plus the token.

    Everything that derives names from the run -- the Execute URL, the anticipated
    output list -- has to agree, so they all go through here rather than reading
    job.args directly.
    """
    args = collections.OrderedDict(
        (key, value) for key, value in job.args.items()
        if not key.startswith(_OPTION_PREFIX))
    token = job.args.get(RUN_TOKEN_OPTION)
    if token:
        base = args.get("results_suffix", "")
        args["results_suffix"] = "%s_%s" % (base, token) if base else token
    return args


def job_to_wps_url(job, asynchronous=True):
    """The WPS Execute URL for a job.

    Asynchronous by default: with storeExecuteResponse the server answers
    immediately with a statusLocation instead of holding the connection open for
    the whole run. Some InVEST models take minutes -- scenic_quality is around
    four -- and a synchronous request means the browser waits that long.
    """
    args = effective_args(job)
    url = job.server.url + "?service=wps&version=1.0.0&request=Execute&IDENTIFIER=" + job.identifier + "&datainputs="
    url = url + ";".join(["%s=%s" % (k, quote(quote(v))) for k, v in args.items()])
    if asynchronous:
        url += "&storeExecuteResponse=true&status=true&ResponseDocument=response"

    return url


# The WPS status values that mean the run is over, one way or the other.
_JOB_FINISHED = {"Succeeded", "Failed"}


def _reachable_via_server(url, server_url):
    """Rewrite a WPS-issued URL onto the host we reach that server on.

    statusLocation and output references carry the address the WPS advertises to
    the outside world (WPS_OUTPUT_URL, the published host port). The dashboard is
    an internal client on the compose network, where that address does not
    resolve, so the path is re-hosted onto whatever we already use to talk to
    the server. Otherwise polling fails silently and a job sits on Accepted
    forever.
    """
    from urllib.parse import urlsplit, urlunsplit
    try:
        target, source = urlsplit(url), urlsplit(server_url)
        if not (target.path and source.netloc):
            return url
        return urlunsplit((source.scheme or target.scheme, source.netloc,
                           target.path, target.query, ""))
    except Exception:  # noqa: BLE001
        return url


def _wps_status(xml):
    """Read the ProcessX state out of an ExecuteResponse."""
    match = re.search(r"Process(Accepted|Started|Paused|Succeeded|Failed)", xml)
    return match.group(1) if match else ""


def job_rerun(request, job_pk):
    """Run a finished job again.

    job_run deliberately will not resubmit a finished job -- that path is the
    status poll -- so running twice is its own action. With the unique-results
    option set, this run gets a fresh suffix and the previous run's outputs stay
    where they are instead of being overwritten.
    """
    job = get_object_or_404(Job, pk=job_pk)
    job.status = "Run"
    job.status_location = ""
    rotate_run_token(job)
    job.save()

    return redirect("job_run", job_pk=job.pk)


def job_status(request, job_pk):
    """Poll the job's statusLocation and advance its recorded status.

    Nothing in the dashboard runs in the background, so this is the moment a
    job's outcome becomes known -- and, once uploads are wired up, where
    anticipated outputs get reconciled against what was really produced.
    """
    job = get_object_or_404(Job, pk=job_pk)

    xml = ""
    if job.status_location:
        try:
            with urllib.request.urlopen(job.status_location, timeout=60) as response:
                xml = response.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 - a poll failure is not fatal
            xml = "<!-- could not read statusLocation: %s -->" % exc

        state = _wps_status(xml)
        if state:
            job.status = state
            job.save()

        if state == "Succeeded":
            try:
                reconcile_uploads(job, xml)
            except Exception as exc:  # noqa: BLE001 - polling must still work
                l = logging.getLogger("django.request")
                l.warning("Could not reconcile uploads for job %s: %s",
                          job.pk, exc)

    if xml.startswith("<?xml") or xml.startswith("<wps"):
        try:
            xml = "\n".join(line for line in parseString(xml).toprettyxml().split("\n")
                            if line.strip())
        except Exception:  # noqa: BLE001 - show it raw if it will not parse
            pass

    return render(request, "wpsclient/job_run.html", {"job": job, "xml": xml})


def job_run(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)

    if job.status == "Validate":
        job.status = "Run"
        job.status_url = job_to_wps_url(job)
        job.save()

        return dashboard(request)

    elif job.status == "Run":
        # Submit and return: the response carries a statusLocation, not results.
        rotate_run_token(job)
        # Reference point for reacting to input changes: a change matters only if
        # it happened after the run that used the data.
        job.args[LAST_RUN_OPTION] = timezone.now().isoformat()
        job.status_url = job_to_wps_url(job)
        try:
            with urllib.request.urlopen(job.status_url, timeout=120) as response:
                xml = response.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            job.status = "Failed"
            job.save()
            return render(request, "wpsclient/job_run.html",
                          {"job": job, "xml": "submit failed: %s" % exc})

        # Anticipated outputs are listed once the run is actually submitted --
        # a job that is only saved may never be run.
        try:
            register_pending(job)
        except Exception as exc:  # noqa: BLE001 - never block a submission
            l.warning("Could not list anticipated outputs: %s", exc)

        location = re.search(r'statusLocation="([^"]+)"', xml)
        if location:
            job.status_location = _reachable_via_server(location.group(1),
                                                        job.server.url)
        job.status = _wps_status(xml) or "Accepted"
        job.save()

        try:
            xml = "\n".join(line for line in parseString(xml).toprettyxml().split("\n")
                            if line.strip())
        except Exception:  # noqa: BLE001
            pass

        return render(request, "wpsclient/job_run.html", {'job': job,
                                                          "xml" : xml})

    elif job.status not in _JOB_FINISHED:
        # Already submitted and still running -- checking on it is a poll.
        return job_status(request, job_pk)

    else:
        return job_detail(request, job_pk)
        


    
