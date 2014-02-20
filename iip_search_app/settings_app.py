# -*- coding: utf-8 -*-

import os

""" Settings for iip_search_app. """


SOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__SOLR_URL') )  # main solr instance

BIBSOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__BIBSOLR_URL') )  # biblio solr instance
