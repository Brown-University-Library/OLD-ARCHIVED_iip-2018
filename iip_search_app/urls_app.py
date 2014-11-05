# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('',

    url( r'^login/$',  'iip_search_app.views.login', name=u'login_url' ),
    url( r'^logout/$',  'iip_search_app.views.logout', name=u'logout_url' ),

    url( r'^results/$',  'iip_search_app.views.iip_results_z', name=u'results_url' ),
    url( r'^results_zotero/$',  'iip_search_app.views.iip_results_z', name=u'z_results_url' ),

    url( r'^search/$',  'iip_search_app.views.iip_results_z', name=u'search_url' ),
    url( r'^search_zotero/$',  'iip_search_app.views.iip_results_z', name=u'z_search_url'),

    # url( r'^viewinscr/(?P<inscrid>.*)/$', 'iip_search_app.views.viewinscr', name=u'inscription_url' ),
    url( r'^viewinscr_zotero/(?P<inscrid>.*)/$', 'iip_search_app.views.viewinscr_zotero', name='inscription_url_zotero'),

    url( r'^view_xml/(?P<inscription_id>.*)/$', 'iip_search_app.views.view_xml', name=u'xml_url' ),

    # url( r'^process/(?P<inscription_id>.*)/$', 'iip_search_app.views.process', name=u'process_url' ),
    url( r'^process/new/$', 'iip_search_app.views.process_new', name=u'process_new_url' ),
    url( r'^process/delete_orphans/$', 'iip_search_app.views.process_orphans', name=u'process_orphans_url' ),
    url( r'^process/all/$', 'iip_search_app.views.process_all', name=u'process_all_url' ),
    url( r'^process/confirm_all/$', 'iip_search_app.views.process_confirm_all', name=u'process_confirm_all_url' ),
    url( r'^process/(?P<inscription_id>.*)/$', 'iip_search_app.views.process_single', name=u'process_single_url' ),

    url( r'^$', redirect_to, {'url': 'search/'} ),

    )
