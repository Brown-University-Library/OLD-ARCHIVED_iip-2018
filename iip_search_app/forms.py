# -*- coding: utf-8 -*-

import logging, re
import solr
from django import forms
from iip_search_app import common, settings_app
import requests
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)


# def facetResults(facet):
#     try:
#         s = solr.SolrConnection( settings_app.SOLR_URL )
#         q = s.select('*:*', **{'facet':'true','facet.field':facet})
#         fc =q.facet_counts['facet_fields'][facet]
#         return fc
#     except Exception as e:
#         log.error( u'in forms.facetResults(); exception, %s' % unicode(repr(e)) )


def doDateEra(self,f,v):
    if f == u'notAfter' and v:
        if self.cleaned_data['beforeDateEra'] == 'bce':
            v = u"-%s" % v.replace('-','')
        elif self.cleaned_data['beforeDateEra'] == 'ce':
            v = u"%s" % v.replace('-','')
        return u"[-10000 TO %s]" % v
    if f == u'notBefore' and v:
        if self.cleaned_data['afterDateEra'] == 'bce':
            v = u"-%s" % v.replace('-','')
        elif self.cleaned_data['afterDateEra'] == 'ce':
            v = u"%s" % v.replace('-','')
        return u"[%s TO 10000]" % v

def make_vocab_list(vocab_dict, solr_facet):
    outlist = []
    for item in solr_facet:
        if item:
            if item in vocab_dict.keys():
                outlist.append((item, vocab_dict[item]))
            else:
                outlist.append((item, item))
    return outlist

class SearchForm( forms.Form ):
    vocab_request = requests.get("http://cds.library.brown.edu/projects/iip/include_taxonomies.xml")
    vocab = ET.fromstring(vocab_request.content)



    # Turns out XPath is only supported in Python 2.7+, and we have to use 2.6...
    # types = [(element.attrib['id'], element.find('catDesc').text) for element in vocab.findall(".//taxonomy[@id='IIP-genre']/category")]
    # physical_types = [(element.attrib['id'], element.find('catDesc').text) for element in vocab.findall(".//taxonomy[@id='IIP-form']/category")]
    # religions = [(element.attrib['id'], element.find('catDesc').text) for element in vocab.findall(".//taxonomy[@id='IIP-religion']/category")]

    # Find all the taxonomy elements
    taxonomies = vocab.findall('{http://www.tei-c.org/ns/1.0}taxonomy')

    # Filter out the three we need
    type_tax = [tax for tax in taxonomies if tax.attrib.values()[0] == 'IIP-genre'][0]
    phys_types_tax = [tax for tax in taxonomies if tax.attrib.values()[0] == 'IIP-form'][0]
    religions_tax = [tax for tax in taxonomies if tax.attrib.values()[0] == 'IIP-religion'][0]

    # Get the xml:id and text of the catDesc element of each category element
    types_dict = dict([(element.attrib.values()[0], element.find('{http://www.tei-c.org/ns/1.0}catDesc').text) for element in type_tax.findall('{http://www.tei-c.org/ns/1.0}category')])
    physical_types_dict = dict([(element.attrib.values()[0], element.find('{http://www.tei-c.org/ns/1.0}catDesc').text) for element in phys_types_tax.findall('{http://www.tei-c.org/ns/1.0}category')])
    religions = [(element.attrib.values()[0], element.find('{http://www.tei-c.org/ns/1.0}catDesc').text) for element in religions_tax.findall('{http://www.tei-c.org/ns/1.0}category')]

    #regions =  [(item, item) for item in sorted( common.facetResults('region').keys())]
    #cities =  [(item, item) for item in sorted( common.facetResults('city').keys())]
    #places = [(val, item) for item, val  in sorted(generatePlaceForm().items()) if item]
    places = [(item, item) for item in sorted( common.facetResults('placeMenu').keys()) if item]
    types =  make_vocab_list(types_dict, sorted( common.facetResults('type').keys()))
    physical_types =  make_vocab_list(physical_types_dict, sorted( common.facetResults('physical_type').keys()))
    languages_dict = {
        "he":"Hebrew",
        "la": "Latin",
        "grc": "Greek",
        "arc": "Aramaic",
        "x-unknown":"Unknown"
    }
    languages = make_vocab_list(languages_dict, sorted( common.facetResults('language').keys()))
    # religions = [(u'"%s"'% item,  u"%s" % item.replace('-',' ')) for item in sorted( common.facetResults('religion').keys()) if item]
    #
    DISPLAY_STATUSES = [
    ('approved', 'Approved'),  # ( 'value', 'label' )
    ('to_approve', 'To Approve'),
    ('to_correct', 'To Correct') ]
    # display_statuses =  [(item, item) for item in sorted( facetResults('display_status').keys() ) if item]
    #
    text = forms.CharField(required=False)
    metadata = forms.CharField(required=False)
    figure = forms.CharField(required=False)
    #region = forms.ChoiceField(required=False, choices=regions, widget=forms.Select)
    #city = forms.ChoiceField(required=False, choices=cities, widget=forms.Select)
    place = forms.MultipleChoiceField(required=False, choices=places, widget=forms.SelectMultiple(attrs={'size':'10'}))
    type = forms.MultipleChoiceField(required=False, choices=types, widget=forms.SelectMultiple(attrs={'size':'7'}))
    physical_type = forms.MultipleChoiceField(required=False, choices=physical_types, widget=forms.SelectMultiple(attrs={'size':'7'}))
    language = forms.MultipleChoiceField(required=False, choices=languages, widget=forms.CheckboxSelectMultiple)
    religion = forms.MultipleChoiceField(required=False, choices=religions, widget=forms.CheckboxSelectMultiple)
    #
    display_status = forms.MultipleChoiceField(required=False, choices=DISPLAY_STATUSES, widget=forms.CheckboxSelectMultiple)
    #
    notBefore = forms.CharField(required=False, max_length=5)
    notAfter = forms.CharField(required=False, max_length=5)
    afterDateEra = forms.ChoiceField(required=False, choices=(('bce','BCE'),('ce','CE')), widget=forms.RadioSelect)
    beforeDateEra = forms.ChoiceField(required=False, choices=(('bce','BCE'),('ce','CE')), widget=forms.RadioSelect)

    def generateSolrQuery(self):
        search_fields = ('text','metadata','figure','region','city','place','type','physical_type','language','religion','notBefore','notAfter', 'display_status')
        response = ''
        first = True
        for f,v in self.cleaned_data.items():
            #The following is specific to the date-encoding in the IIP & US Epigraphy projects
            #If youre using this code for other projects, you probably want to omit them
            if ((f == u'notBefore') or (f == u'notAfter')) and v:
                v = doDateEra(self,f,v)
            # End custom blocks
            elif v:
                if isinstance(v, list):
                    vListFirst = True
                    vlist = ''
                    for c in v:
                        if re.search('\s', unicode(c)):
                            c = u"\"%s\"" % c
                        if vListFirst:
                            vListFirst = False
                        else:
                            vlist += " OR " if not ((f == u'religion') or (f == u'language')) else " AND "
                        vlist += u"%s" % c
                    v = u"(%s)" % vlist
                else:
                    if re.search('\s', unicode(v)):
                        v = u"\"%s\"" % v
            if f and v:
                if f in search_fields:
                    if first:
                        first = False
                    else:
                        if(v != ''): response += " AND "
                    if(v != ''): response += u"%s:%s" % (f,v)
        return response


# class SearchForm(forms.Form):
#     #regions =  [(item, item) for item in sorted(facetResults('region').keys())]
#     #cities =  [(item, item) for item in sorted(facetResults('city').keys())]
#     #places = [(val, item) for item, val  in sorted(generatePlaceForm().items()) if item]
#     places = [(item, item) for item in sorted(facetResults('placeMenu').keys()) if item]
#     types =  [(item, item) for item in sorted(facetResults('type').keys()) if item]
#     physical_types =  [(item, item) for item in sorted(facetResults('physical_type').keys()) if item]
#     languages = [(item, u"%s" % item.replace('-',' ')) for item in sorted(facetResults('language').keys()) if item]
#     religions = [(u'"%s"'% item,  u"%s" % item.replace('-',' ')) for item in sorted(facetResults('religion').keys()) if item]
#     #
#     # display_statuses =  [(item, item) for item in sorted( facetResults('display_status').keys() ) if item]
#     #
#     text = forms.CharField(required=False)
#     metadata = forms.CharField(required=False)
#     figure = forms.CharField(required=False)
#     #region = forms.ChoiceField(required=False, choices=regions, widget=forms.Select)
#     #city = forms.ChoiceField(required=False, choices=cities, widget=forms.Select)
#     place = forms.MultipleChoiceField(required=False, choices=places, widget=forms.SelectMultiple(attrs={'size':'10'}))
#     type = forms.MultipleChoiceField(required=False, choices=types, widget=forms.SelectMultiple(attrs={'size':'7'}))
#     physical_type = forms.MultipleChoiceField(required=False, choices=physical_types, widget=forms.SelectMultiple(attrs={'size':'7'}))
#     language = forms.MultipleChoiceField(required=False, choices=languages, widget=forms.CheckboxSelectMultiple)
#     religion = forms.MultipleChoiceField(required=False, choices=religions, widget=forms.CheckboxSelectMultiple)
#     #
#     display_status = forms.MultipleChoiceField(required=False, choices=display_statuses, widget=forms.CheckboxSelectMultiple)
#     #
#     notBefore = forms.CharField(required=False, max_length=5)
#     notAfter = forms.CharField(required=False, max_length=5)
#     afterDateEra = forms.ChoiceField(required=False, choices=(('bce','BCE'),('ce','CE')), widget=forms.RadioSelect)
#     beforeDateEra = forms.ChoiceField(required=False, choices=(('bce','BCE'),('ce','CE')), widget=forms.RadioSelect)
#
#     def generateSolrQuery(self):
#         search_fields = ('text','metadata','figure','region','city','place','type','physical_type','language','religion','notBefore','notAfter', 'display_status')
#         response = ''
#         first = True
#         for f,v in self.cleaned_data.items():
#             #The following is specific to the date-encoding in the IIP & US Epigraphy projects
#             #If youre using this code for other projects, you probably want to omit them
#             if ((f == u'notBefore') or (f == u'notAfter')) and v:
#                 v = doDateEra(self,f,v)
#             # End custom blocks
#             elif v:
#                 if isinstance(v, list):
#                     vListFirst = True
#                     vlist = ''
#                     for c in v:
#                         if re.search('\s', unicode(c)):
#                             c = u"\"%s\"" % c
#                         if vListFirst:
#                             vListFirst = False
#                         else:
#                             vlist += " OR "
#                         vlist += u"%s" % c
#                     v = u"(%s)" % vlist
#                 else:
#                     if re.search('\s', unicode(v)):
#                         v = u"\"%s\"" % v
#             if f and v:
#                 if f in search_fields:
#                     if first:
#                         first = False
#                     else:
#                         response += " AND "
#                     response += u"%s:%s" % (f,v)
#         return response
