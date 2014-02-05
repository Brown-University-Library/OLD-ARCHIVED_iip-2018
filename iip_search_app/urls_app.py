# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to
# from usep_app import settings_app


urlpatterns = patterns('',

    url( r'^hello/$',  'iip_search_app.views.hello', name=u'hello_url' ),

    url( r'^search/$',  'iip_search_app.views.iip_results', name=u'search_iip_results_url' ),

    # ( r'^$', redirect_to, {'url': '/%s/collections/' % settings_app.PROJECT_APP} ),

    )
