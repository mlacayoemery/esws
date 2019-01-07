from django.conf.urls import url
from . import views

urlpatterns = [
    ##server specific urls
    url(r'^$', views.dashboard, name='dashboard'),    
    url(r'^server/(?P<server_type>CSV|WCS|WFS|WPS)/$', views.server_list, name='server_list'),
    url(r'^server/(?P<server_type>CSV|WCS|WFS|WPS)/(?P<server_pk>\d+)/$', views.server_detail, name='server_detail'),
    url(r'^server/(?P<server_type>CSV|WCS|WFS|WPS)/new/$', views.server_new, name='server_new'),
    url(r'^server/(?P<server_type>CSV|WCS|WFS|WPS)/(?P<server_pk>\d+)/edit/$', views.server_edit, name='server_edit'),

    url(r'^server/(?P<server_type>WPS)/(?P<server_pk>\d+)/describe/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.server_wps_describe_process, name='server_wps_describe_process'),

    url(r'^server/(?P<server_type>CSV|WCS|WPS|WFS)/(?P<server_pk>\d+)/elements/$', views.server_element_list, name='server_element_list'),
    url(r'^server/(?P<server_type>CSV|WCS|WPS|WFS)/(?P<server_pk>\d+)/register/(?P<process_id>[-a-zA-Z0-9_:.]+)/$', views.server_element_register, name='server_element_register'),    
    ##job specific urls
    url(r'^job/$', views.job_list, name='job_list'),
    #add server specific job list
    url(r'^server/(?P<server_pk>\d+)/jobs/$', views.server_job_list, name='server_job_list'),
    
    url(r'^job/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_detail, name='job_detail'),
    url(r'^job/(?P<process_pk>[a-zA-Z0-9_:]+)/edit/$', views.job_edit, name='job_edit'),
    
    url(r'^server/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.job_new, name='job_new'),
    #url(r'^server/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/edit/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_edit, name='job_edit'),

##    url(r'^test/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_edit_json, name='job_edit_json'),
##    url(r'^test/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.job_new_wps, name='job_new_wps'),
]
