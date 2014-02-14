# -*- coding: utf-8 -*-

import random


def get_log_identifier( request_session=None ):
    """ Returns a log_identifier unicode_string.
        Sets it in the request session if necessary. """
    log_identifier = unicode( random.randint(1000,9999) )
    if request_session == None:  # cron script writing to log
        pass
    else:
        if u'log_identifier' in request_session:
            log_identifier = request_session[u'log_identifier']
        else:
            request_session[u'log_identifier'] = log_identifier
    return log_identifier


def paginateRequest(qstring,resultsPage,log_identifier):
  try:
    s = solr.SolrConnection( settings_app.SOLR_URL )
    args = {'rows':25}
    try:
      q = s.query((qstring.encode('utf-8')),**args)
      updateLog( '- in common.paginateRequest(); q created via try.', log_identifier )
    except:
      q = s.query('*:*', **args)
      updateLog( '- in common.paginateRequest(); q created via except.', log_identifier )
    try:
      fq = s.query((qstring.encode('utf-8')),facet='true', facet_field=['region','city','type','physical_type','language','religion'],**args)
    except:
      fq = s.query('*:*',facet='true', facet_field=['region','city','type','physical_type','language','religion'],**args)
    updateLog( '- in common.paginateRequest(); q is: %s -- q.__dict__ is: %s' % (q,q.__dict__), log_identifier )
    p = solr.SolrPaginator(q, 25)
    try:
      pg = p.page(resultsPage)
    except:
      pg = ''
    try:
      f = fq.facet_counts['facet_fields']
    except:
      f  = ''
    #sorted_f = sorted(f.items(), key=operator.itemgetter(1))
    #facets = dict(sorted_f)
    dispQstring = queryCleanup(qstring.encode('utf-8'))
    return {'pages': p, 'iipResult': pg, 'qstring':qstring, 'resultsPage': resultsPage, 'facets':f, 'dispQstring': dispQstring}
  except:
    message = makeErrorString()
    updateLog( '- in common.paginateRequest(); error: %s' % message, log_identifier, message_importance='high' )
    return { 'error_message': message }
  # end def paginateRequest()


def updateQstring( initial_qstring, session_authz_dict, log_identifier ):
    """ Adds 'approved' display-status limit to solr query string if user is *not* logged in
          (because if user *is* logged in, display facets are shown explicitly).
        Returns modified_qstring dict.
        Called by: views.iipResults(). """
    if ( (session_authz_dict == None)
         or (not u'authorized' in session_authz_dict)
         or (not session_authz_dict['authorized'] == True) ):
        qstring = u'display_status:(approved) AND ' + initial_qstring
    else:
        qstring = initial_qstring
    return { 'modified_qstring': qstring }
