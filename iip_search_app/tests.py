"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import pprint
from iip_search_app import forms
from django.test import TestCase


class FormsTest( TestCase ):

    def test_facet_solr_query( self ):
        """ Checks type of data returned from query. """
        facet_count_dict = forms.facetResults( facet=u'placeMenu' )
        # pprint.pprint( facet_count_dict )
        for place in [  u'Galilee', u'Judaea', u'Lower Galilee' ]:
            self.assertEqual(
                place in facet_count_dict.keys(), True )
            self.assertEqual(
                type(facet_count_dict[place]) == int, True )


# class SimpleTest(TestCase):
#     def test_basic_addition(self):
#         """
#         Tests that 1 + 1 always equals 2.
#         """
#         self.assertEqual(1 + 1, 2)
