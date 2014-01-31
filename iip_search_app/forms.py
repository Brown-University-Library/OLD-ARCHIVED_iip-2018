# -*- coding: utf-8 -*-

from django import forms
from iip_search_app import common
# from iipSearch import common, settings_app
# import solr
# import re, urllib


def facetResults(facet):
  try:
    s = solr.SolrConnection( settings_app.SOLR_URL )
    # common.updateLog( '- in forms.facetResults(); s is: %s -- s.__dict__ is: %s' % (s, s.__dict__) )
    q = s.query('*:*', **{'facet':'true','facet.field':facet})
    # common.updateLog( '- in forms.facetResults(); facet is: %s; q.__dict__ is: %s' % (facet, q.__dict__) )
    fc =q.facet_counts['facet_fields'][facet]
    return fc
  except:
    message = common.makeErrorString()
    common.updateLog( '- in forms.facetResults(); error: %s' % message, message_importance='high' )
    return { 'error_message': message }


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


class SearchForm( forms.Form ):
    #regions =  [(item, item) for item in sorted(facetResults('region').keys())]
    #cities =  [(item, item) for item in sorted(facetResults('city').keys())]
    #places = [(val, item) for item, val  in sorted(generatePlaceForm().items()) if item]
    places = [(item, item) for item in sorted(facetResults('placeMenu').keys()) if item]
    types =  [(item, item) for item in sorted(facetResults('type').keys()) if item]
    physical_types =  [(item, item) for item in sorted(facetResults('physical_type').keys()) if item]
    languages = [(item, u"%s" % item.replace('-',' ')) for item in sorted(facetResults('language').keys()) if item]
    religions = [(u'"%s"'% item,  u"%s" % item.replace('-',' ')) for item in sorted(facetResults('religion').keys()) if item]
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
                            vlist += " OR "
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
                        response += " AND "
                    response += u"%s:%s" % (f,v)
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


