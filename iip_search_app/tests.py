# -*- coding: utf-8 -*-

import pprint
import solr
from iip_search_app import common, settings_app
from django.test import TestCase


class CommonTest( TestCase ):
    """ Tests functions in 'common.py'. """

    def test_facetResults( self ):
        """ Checks type of data returned from query. """
        facet_count_dict = common.facetResults( facet=u'placeMenu' )
        for place in [  u'Galilee', u'Judaea', u'Lower Galilee' ]:
            self.assertEqual(
                True,
                place in facet_count_dict.keys()
                )
            self.assertEqual(
                True,
                type(facet_count_dict[place]) == int
                )

    def test_fetchBiblio( self ):
        """ Checks biblio solr response for a given iip solr resultset and target-string. """
        s = solr.SolrConnection( settings_app.SOLR_URL )
        qstring = u'inscription_id:%s' % u'beth0282'
        q = s.query( qstring )
        result = common.fetchBiblio( q_results=q.results, target=u'biblTranslation'.encode(u'utf-8') )
        self.assertEqual(
            list, type(result)
            )
        self.assertEqual(
            1, len(result)
            )
        self.assertEqual(
            dict, type( result[0] )
            )
        self.assertEqual(
            23, len( result[0].keys() )
            )
        self.assertEqual(
            [u'biblioId', u'publisher_place_t', u'subject_facet', u'subject_geographic_t'],
            sorted( result[0].keys()[0:4] )
            )

    def test_paginateRequest( self ):
        """ Checks data returned by paginateRequest. """
        sent_qstring = u'display_status:(approved) AND language:(Aramaic)'
        sent_results_page = 3
        data = common.paginateRequest( qstring=sent_qstring, resultsPage=sent_results_page, log_id=u'123' )
        self.assertEqual(
            [u'dispQstring', u'facets', u'iipResult', u'pages', u'qstring', u'resultsPage'],
            sorted( data.keys() )
            )
        self.assertEqual(
            u'display status:approved AND language:Aramaic',
            data[u'dispQstring']
            )
        self.assertEqual(
            [u'city', u'language', u'physical_type', u'region', u'religion', u'type'],
            sorted( data[u'facets'].keys() )
            )
        self.assertEqual(
            True,
            u'<solr.paginator.SolrPage instance' in unicode(repr(data[u'iipResult']))
            )
        self.assertEqual(
            sent_qstring,
            data[u'qstring']
            )
        self.assertEqual(
            True,
            u'<solr.paginator.SolrPaginator instance' in unicode(repr(data[u'pages']))
            )
        self.assertEqual(
            sent_results_page,
            data[u'resultsPage']
            )

    def test_update_q_string( self ):
        """ Tests modification of solr query string. """
        initial_qstring = u'foo'
        log_identifier = u'bar'
        # no session_authz_dict
        session_authz_dict = None
        self.assertEqual(
            {'modified_qstring': u'display_status:(approved) AND foo'},
            common.updateQstring(initial_qstring, session_authz_dict, log_identifier) )
        # session_authz_dict, but no 'authorized' key
        session_authz_dict = { u'some_key': u'some_value' }
        self.assertEqual(
            {'modified_qstring': u'display_status:(approved) AND foo'},
            common.updateQstring(initial_qstring, session_authz_dict, log_identifier) )
        # session_authz_dict, and 'authorized' key, but authorized not True
        session_authz_dict = { u'authorized': u'other_than_true' }
        self.assertEqual(
            {'modified_qstring': u'display_status:(approved) AND foo'},
            common.updateQstring(initial_qstring, session_authz_dict, log_identifier) )
        # life good
        session_authz_dict = { u'authorized': True }
        self.assertEqual(
            {'modified_qstring': u'foo'},
            common.updateQstring(initial_qstring, session_authz_dict, log_identifier) )
