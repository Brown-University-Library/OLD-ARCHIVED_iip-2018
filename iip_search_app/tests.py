# -*- coding: utf-8 -*-

import json, logging, pprint
import requests, solr
from iip_search_app import common, models, settings_app
from django.test import TestCase
from models import Processor, ProcessorUtils


log = logging.getLogger(__name__)


class CommonTest( TestCase ):
    """ Tests functions in 'common.py'. """

    def test_facetResults( self ):
        """ Checks type of data returned from query. """
        facet_count_dict = common.facetResults( facet=u'placeMenu' )
        log.debug( u'facet_count_dict, ```%s```' % pprint.pformat(facet_count_dict) )
        for place in [  u'Galilee', u'Jordan', u'Judaea' ]:
            self.assertEqual(
                True,
                place in facet_count_dict.keys()
                )
            self.assertEqual(
                True,
                type(facet_count_dict[place]) == int
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

    def test_validate_xml( self ):
        """ Tests validation. """
        schema = u"""<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<xsd:element name="a" type="AType"/>
    <xsd:complexType name="AType">
        <xsd:sequence>
            <xsd:element name="b" type="xsd:string" />
        </xsd:sequence>
    </xsd:complexType>
</xsd:schema>"""
        ## valid
        xml = u"""<?xml version="1.0" encoding="utf-8"?><a><b></b></a>"""
        data_dict = common.validate_xml( xml=xml, schema=schema )
        self.assertEqual(
            True,
            data_dict[u'validate_result'] )
        ## not valid
        xml = u"""<?xml version="1.0" encoding="utf-8"?><a><c></c></a>"""
        data_dict = common.validate_xml( xml=xml, schema=schema )
        self.assertEqual(
            False,
            data_dict[u'validate_result'] )

    def test_check_xml_wellformedness(self):
        """ Tests that xml is well-formed.
            TODO: eliminate this test and the code once there's a schema, and instead use validate_xml() """
        ## good
        xml = u"""<?xml version="1.0" encoding="utf-8"?><a><b></b></a>"""
        data_dict = common.check_xml_wellformedness( xml )
        self.assertEqual(
            True,
            data_dict[u'well_formed'] )
        ## bad
        xml = u"""<a><b><b></a>"""
        data_dict = common.check_xml_wellformedness( xml )
        self.assertEqual(
            False,
            data_dict[u'well_formed'] )

    ## start test_update_display_status()

    def test_update_display_status(self):
        """ Tests updated solr display-status. """
        ## setup
        ( SOLR_URL, TEST_INSCRIPTION_ID, solr_query_url, current_status_to_new_button_click_dict ) = self._setup_update_display_status_test()
        current_display_status = self._get_current_display_status( item_id=settings_app.TEST_INSCRIPTION_ID, query_url=solr_query_url )
        result_dict = common.update_display_status(
            button_action=current_status_to_new_button_click_dict[current_display_status],
            item_id=TEST_INSCRIPTION_ID,
            query_url=u'%s/select/' % settings_app.SOLR_URL,
            update_url=SOLR_URL )
        checked_display_status = self._get_current_display_status( item_id=TEST_INSCRIPTION_ID, query_url=solr_query_url )
        ## tests
        self.assertEqual(
            True,
            current_display_status in [u'approved', u'to_approve', u'to_correct'] )
        self.assertEqual(
            [ u'button_clicked', u'new_display_status', u'solr_response_status' ],
            sorted(result_dict.keys()) )
        self.assertEqual(
            checked_display_status,
            result_dict[u'new_display_status'] )

    def _setup_update_display_status_test(self):
        """ Helper function.
            Prepares variables.
            Returns tuple of variables.
            Called by test_update_display_status(). """
        SOLR_URL = settings_app.SOLR_URL
        TEST_INSCRIPTION_ID = settings_app.TEST_INSCRIPTION_ID
        solr_query_url = u'%s/select/' % settings_app.SOLR_URL
        current_status_to_new_button_click_dict = {  # simulates a button-click given the current-status
            u'approved': u'To Correct',
            u'to_correct': u'To Approve',
            u'to_approve': u'Approved' }
        return ( SOLR_URL, TEST_INSCRIPTION_ID, solr_query_url, current_status_to_new_button_click_dict )

    def _get_current_display_status( self, item_id, query_url ):
        """ Helper function.
            Takes item_id string.
            Performs solr lookup.
            Returns the solr display_status.
            Called by update_display_status(). """
        payload = { u'q': u'inscription_id:%s' % item_id, u'indent': u'on', u'wt': u'json' }
        r = requests.get( query_url, params=payload )  # url like: 'http://solr_url/solr/iip/select/?q=inscription_id%3Aakas0001&indent=on'
        current_data_dict = r.json()
        docs = current_data_dict[u'response'][u'docs']
        doc_dict = docs[0]
        return doc_dict[u'display_status']

    ## end test_update_display_status()

    ## end class Common()


class ProcessorUtilsTest( TestCase ):
    """ Tests functions in 'models.py' ProcessorUtils() """

    def test_call_svn_update( self ):
        """ Tests envoy output command. """
        utils = ProcessorUtils()
        result = utils.call_svn_update()
        # print u'- envoy result...'; pprint.pprint( result )
        self.assertEqual(
            u'Updating',
            result[u'std_out'].split()[0] )
        self.assertEqual(
            True,
            u'Updated to revision' in result[u'std_out'] or u'At revision' in result[u'std_out'] )

    def test_parse_update_output( self ):
        """ Tests for sorted file_ids when files found. """
        utils = ProcessorUtils()
        ## tests regular xml output
        dummy_stdout = u"""Updating '/path/to/iip/xml':\nU    /path/to/iip/xml/zoor0102.xml\nU    /path/to/iip/xml/beth0068.xml\nA    /path/to/iip/xml/zoor0261.xml\nA  """
        result = utils.parse_update_output( dummy_stdout )
        self.assertEqual( [
            u'beth0068', u'zoor0102', u'zoor0261' ],
            result[u'file_ids'] )
        ## tests empty output
        dummy_stdout = u"""Updating '/path/to/iip/xml':\nU    Updated to revision 11969.\n"""
        result = utils.parse_update_output( dummy_stdout )
        self.assertEqual(
            [],
            result[u'file_ids'] )


# eof
