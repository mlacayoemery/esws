from django.conf.urls import url
from . import views

urlpatterns = [
    ##server specific urls
    url(r'^$', views.dashboard, name='dashboard'),    
    url(r'^server/$', views.server_list, name='server_list'),
    url(r'^server/(?P<server_pk>\d+)/$', views.server_detail, name='server_detail'),
    url(r'^server/new/$', views.server_new, name='server_new'),
    url(r'^server/(?P<server_pk>\d+)/edit/$', views.server_edit, name='server_edit'),
    url(r'^server/(?P<server_pk>\d+)/capabilities/$', views.server_capabilities, name='server_capabilities'),
    url(r'^server/(?P<server_pk>\d+)/describe/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.server_describe_process, name='server_describe_process'),

    ##job specific urls
    url(r'^jobs/$', views.job_list, name='job_list'),
    #add server specific job list
    url(r'^server/(?P<server_pk>\d+)/jobs/$', views.server_job_list, name='server_job_list'),
    
    url(r'^jobs/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_detail, name='job_detail'),
    url(r'^jobs/(?P<process_pk>[a-zA-Z0-9_:]+)/edit/$', views.job_edit, name='job_edit'),
    
    url(r'^server/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.job_new, name='job_new'),
    #url(r'^server/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/edit/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_edit, name='job_edit'),

##    url(r'^test/(?P<process_pk>[a-zA-Z0-9_:]+)/$', views.job_edit_json, name='job_edit_json'),
##    url(r'^test/(?P<server_pk>\d+)/execute/(?P<process_id>[a-zA-Z0-9_:]+)/$', views.job_new_wps, name='job_new_wps'),
]
