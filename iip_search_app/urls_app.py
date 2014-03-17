# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to
# from usep_app import settings_app


urlpatterns = patterns('',

    url( r'^hello/$',  'iip_search_app.views.hello', name=u'hello_url' ),

    url( r'^login/$',  'iip_search_app.views.login', name=u'login_url' ),
    url( r'^logout/$',  'iip_search_app.views.logout', name=u'logout_url' ),

    url( r'^results/$',  'iip_search_app.views.iip_results', name=u'results_url' ),

    url( r'^search/$',  'iip_search_app.views.iip_results', name=u'search_url' ),

    url( r'^viewinscr/(?P<inscrid>.*)/$', 'iip_search_app.views.viewinscr', name=u'inscription_url' ),

    url( r'^process/(?P<inscription_id>.*)/$', 'iip_search_app.views.process', name=u'process_url' ),

    url( r'^$', redirect_to, {'url': 'search/'} ),

    )
