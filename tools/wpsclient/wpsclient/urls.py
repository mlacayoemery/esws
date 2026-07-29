from django.urls import re_path as url
from . import views

# Slashes are allowed: CSV elements are paths relative to the file server root
# (get_ows_data_url joins them as "<server_url>/<identifier>"), so nested sample
# data like "invest/pollination/guild_table.csv" has to round-trip. The patterns
# using this are anchored and the preceding segments are fixed, so the greedy
# match still ends at the trailing slash.
element_id = '[-a-zA-Z0-9_:./]+'
server_title = '[a-zA-Z0-9\W]+'
server_url = 'http[a-zA-Z0-9:./]+'
server_type = 'CSV|WCS|WFS|WPS|TPL'

urlpatterns = [
    ##server specific urls
    url(r'^$', views.dashboard, name='dashboard'),    
    url(r'^server/(?P<server_type>'+server_type+')/$', views.server_list, name='server_list'),
    url(r'^server/(?P<server_type>'+server_type+')/(?P<server_pk>\d+)/$', views.server_detail, name='server_detail'),
    url(r'^server/(?P<server_type>'+server_type+')/new/$', views.server_new, name='server_new'),

    url(r'^server/(?P<server_type>'+server_type+')/register/(?P<title>'+server_title+')/url/(?P<url>'+server_url+')$', views.server_register, name='server_register'),
    
    url(r'^server/(?P<server_type>'+server_type+')/(?P<server_pk>\d+)/edit/$', views.server_edit, name='server_edit'),

    url(r'^server/(?P<server_type>'+server_type+')/(?P<server_pk>\d+)/element/(?P<element_id>'+element_id+')/$', views.server_element_detail, name='server_element_detail'),

    url(r'^server/(?P<server_type>'+server_type+')/(?P<server_pk>\d+)/element/$', views.server_element_list, name='server_element_list'),
    url(r'^server/(?P<server_type>'+server_type+')/(?P<server_pk>\d+)/register/(?P<element_id>'+element_id+')/$', views.server_element_register, name='server_element_register'),
    url(r'^server/(?P<server_type>'+server_type+')/(?P<server_pk>\d+)/unregister/(?P<element_id>'+element_id+')/$', views.server_element_unregister, name='server_element_unregister'),
    
    ##job specific urls
    url(r'^job/$', views.job_list, name='job_list'),
    #add server specific job list
    url(r'^server/(?P<server_pk>\d+)/job/$', views.server_job_list, name='server_job_list'),
    
    url(r'^job/(?P<job_pk>[a-zA-Z0-9_\.:]+)/$', views.job_detail, name='job_detail'),
    url(r'^job/(?P<job_pk>[a-zA-Z0-9_\.:]+)/edit/$', views.job_edit, name='job_edit'),

    
    url(r'^server/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_\.:]+)/$', views.job_new, name='job_new'),

    url(r'^server/(?P<server_pk>\d+)/job/(?P<process_id>[a-zA-Z0-9_\.:]+)/new/(?P<args>[a-zA-Z0-9_%\./:\-]+)$', views.job_new_dynamic, name='job_new_dynamic'),
    
    #url(r'^server/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/edit/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_edit, name='job_edit'),

##    url(r'^test/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_edit_json, name='job_edit_json'),
##    url(r'^test/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.job_new_wps, name='job_new_wps'),
    url(r'^test/wy/$', views.water_yield, name='water_yield'),
    url(r'^job/(?P<job_pk>[a-zA-Z0-9_:]+)/run/$', views.job_run, name='job_run'),    
]
