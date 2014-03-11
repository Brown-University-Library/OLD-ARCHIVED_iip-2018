# -*- coding: utf-8 -*-

import json, pprint
import requests, solr
from iip_search_app import common, models, settings_app
from django.test import TestCase
from models import Processor


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
        ## valid
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

    ## end class Common()


class ProcessorTest( TestCase ):
    """ Tests functions in 'models.py' Processor() """

    # def test_process_file__check_keys( self ):
    #     """ Tests keys. """
    #     from models import Processor
    #     p = Processor()
    #     self.assertEqual(
    #         [u'a__svn_export', u'b__grab_source_xml', u'c__run_munger', u'd__make_initial_solr_doc', u'e__update_display_facet', u'f__post_to_solr'],
    #         sorted(p.process_file(u'dummy_id').keys()) )

    def test_grab_latest_file( self ):
        """ Tests keys; no-errors; and success-message. """
        p = Processor()
        data_dict = p.grab_latest_file( file_id=u'beth0282' )
        self.assertEqual(
            [u'stderr', u'stdout', u'submitted_destination_path', u'submitted_file_id', u'submitted_vc_url'],
            sorted(data_dict.keys()) )
        self.assertEqual(
            [],
            data_dict[u'stderr'] )
        self.assertEqual(
            True,
            u'Export complete' in data_dict[u'stdout'][1] )

    def test_grab_original_xml( self ):
        """ Tests for well-formed xml and type of returned string.
            TODO: update to check for _valid_ xml once I have access to a schema. """
        p = Processor()
        grab_dict = p.grab_original_xml( file_id=u'beth0282' )
        ## type check
        self.assertEqual(
            unicode,
            type(grab_dict[u'xml']) )
        ## well-formedness check
        well_formedness_dict = common.check_xml_wellformedness( xml=grab_dict[u'xml'] )
        self.assertEqual(
            True,
            well_formedness_dict[u'well_formed']
            )

    def test_run_munger( self ):
        """ Tests for well-formed xml and type of returned string.
            TODO: update to check for _valid_ xml once I have access to a schema. """
        p = Processor()
        grab_dict = p.grab_original_xml( file_id=u'beth0282' )
        munger_dict = p.run_munger( source_xml=grab_dict[u'xml'] )
        ## type check
        self.assertEqual(
            unicode,
            type(munger_dict[u'munged_xml']) )
        ## well-formedness check
        well_formedness_dict = common.check_xml_wellformedness( xml=munger_dict[u'munged_xml'] )
        self.assertEqual(
            True,
            well_formedness_dict[u'well_formed']
            )

    def test_make_initial_solr_doc( self ):
        """ Tests for well-formed xml and type of returned string.
            TODO: update to check for _valid_ xml once I have access to a schema. """
        p = Processor()
        grab_dict = p.grab_original_xml( file_id=u'beth0282' )
        munger_dict = p.run_munger( source_xml=grab_dict[u'xml'] )
        initial_doc_dict = p.make_initial_solr_doc( munger_dict[u'munged_xml'] )
        ## type check
        self.assertEqual(
            unicode,
            type(initial_doc_dict[u'transformed_xml']) )
        ## well-formedness check
        well_formedness_dict = common.check_xml_wellformedness( xml=initial_doc_dict[u'transformed_xml'] )
        self.assertEqual(
            True,
            well_formedness_dict[u'well_formed']
            )

    def test_update_display_facet( self ):
        """ Tests for well-formed xml and type of returned string.
            TODO: update to check for _valid_ xml once I have access to a schema. """
        p = Processor()
        grab_dict = p.grab_original_xml( file_id=u'beth0282' )
        munger_dict = p.run_munger( source_xml=grab_dict[u'xml'] )
        initial_doc_dict = p.make_initial_solr_doc( munger_dict[u'munged_xml'] )
        updated_disply_dict = p.update_display_facet( initial_solr_xml=initial_doc_dict[u'transformed_xml'], display_status=u'to_approve' )
        ## type check
        self.assertEqual(
            unicode,
            type(updated_disply_dict[u'updated_xml']) )
        ## well-formedness check
        well_formedness_dict = common.check_xml_wellformedness( xml=updated_disply_dict[u'updated_xml'] )
        self.assertEqual(
            True,
            well_formedness_dict[u'well_formed'] )

    def test_update_solr( self ):
        """ Tests solr response, and a before and after solr-query result. """
        p = Processor()
        # initial query
        url = u'http://worfdev.services.brown.edu:8080/solr/iip_proofread/select?q=display_status:(to_approve)&wt=json&start=1&rows=1'  # second record
        r = requests.get( url )
        initial_dict = json.loads( r.content )
        initial_document = initial_dict[u'response'][u'docs'][0]
        initial_id = initial_dict[u'response'][u'docs'][0][u'inscription_id']
        # process new item
        grab_dict = p.grab_original_xml( file_id=initial_id )
        munger_dict = p.run_munger( source_xml=grab_dict[u'xml'] )
        initial_doc_dict = p.make_initial_solr_doc( munger_dict[u'munged_xml'] )
        updated_disply_dict = p.update_display_facet( initial_solr_xml=initial_doc_dict[u'transformed_xml'], display_status=u'to_approve' )
        update_solr_dict = p.update_solr( updated_disply_dict[u'updated_xml'] )
        # test response
        self.assertEqual(
            200,
            update_solr_dict[u'response_status_code']
            )
        # test before and after
        url = u'http://worfdev.services.brown.edu:8080/solr/iip_proofread/select?q=inscription_id:%s&wt=json' % initial_id
        r = requests.get( url )
        after_dict = json.loads( r.content )
        after_document = after_dict[u'response'][u'docs'][0]
        for ( key, initial_value ) in initial_document.items():
            after_value = after_document[key]
            self.assertEqual(
                initial_value,
                after_value
                )


# eof
