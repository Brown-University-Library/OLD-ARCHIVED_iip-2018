# -*- coding: utf-8 -*-

import json, os

""" Settings for iip_search_app. """


SOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__SOLR_URL') )  # main solr instance
BIBSOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__BIBSOLR_URL') )  # biblio solr instance

DEV_AUTH_HACK = unicode( os.environ.get(u'IIP_SEARCH__DEV_AUTH_HACK') )  # 'enabled' or 'disabled' (only enabled for local non-shib development)
LEGIT_ADMINS = json.loads( unicode(os.environ.get(u'IIP_SEARCH__LEGIT_ADMINS')) )  # json shib-eppn list

URL_SCHEME = unicode( os.environ.get(u'IIP_SEARCH__URL_SCHEME') )  # 'http' or, on production, 'https'

# end
