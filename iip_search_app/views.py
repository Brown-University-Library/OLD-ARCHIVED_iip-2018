# -*- coding: utf-8 -*-

import logging
import solr
from django.http import HttpResponse
from django.shortcuts import render_to_response, render
from iip_search_app import common, settings_app
from iip_search_app.utils import ajax_snippet
from iip_search_app.forms import SearchForm

log = logging.getLogger(__name__)


## search and results ##

def iip_results( request ):
    """ Handles /search/ GET, POST, and ajax-GET. """
    log_id = common.get_log_identifier( request.session )
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    if request.method == u'POST':  # form has been submitted by user
        return render( request, u'iip_search_templates/base_extend.html', _get_POST_context(request) )
    elif request.is_ajax():  # user has requested another page, a facet, etc.
        return HttpResponse( _get_ajax_unistring(request) )
    else:  # regular GET
        return render( request, u'iip_search_templates/search_form.html', _get_GET_context(request) )

def _get_POST_context( request ):
    """ Returns correct context for POST.
        Called by iip_results() """
    request.encoding = u'utf-8'
    form = SearchForm( request.POST ) # form bound to the POST data
    if form.is_valid():
        initial_qstring = form.generateSolrQuery()
        resultsPage = 1
        updated_qstring = common.updateQstring(
            initial_qstring=initial_qstring, session_authz_dict=request.session['authz_info'], log_id=common.get_log_identifier(request.session) )['modified_qstring']
        context = common.paginateRequest(
            qstring=updated_qstring, resultsPage=resultsPage, log_id=common.get_log_identifier(request.session) )
        context[u'session_authz_info'] = request.session[u'authz_info']
        return context

def _get_ajax_unistring( request ):
    """ Returns unicode string based on ajax update.
        Called by iip_results() """
    log_id = common.get_log_identifier(request.session)
    log.info( u'in views._get_ajax_unistring(); id, %s; starting' % log_id )
    initial_qstring = request.GET.get( u'qstring', u'*:*' )
    updated_qstring = common.updateQstring( initial_qstring, request.session[u'authz_info'], log_id )[u'modified_qstring']
    resultsPage = int( request.GET[u'resultsPage'] )
    context = common.paginateRequest(
        qstring=updated_qstring, resultsPage=resultsPage, log_id=log_id )
    return_str = ajax_snippet.render_block_to_string(u'iip_search_templates/base_extend.html', u'content', context)
    return unicode( return_str )

def _get_GET_context( request ):
    """ Returns correct context for GET.
        Called by iip_results() """
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    log.debug( u'in views._get_GET_context(); about to instantiate form' )
    form = SearchForm()  # an unbound form
    log.debug( u'in views._get_GET_context(); form instantiated' )
    context = {
        u'form': form,
        u'session_authz_info': request.session[u'authz_info'],
        u'settings_app': settings_app }
    log.debug( u'in views._get_GET_context(); context, %s' % context )
    return context


## view inscription ##

def viewinscr( request, inscrid ):
    # return HttpResponse( u'<p>%s</p>' % inscrid )
    try:
        log.debug( u'in views.viewinscr(); starting' )
        log_identifier = common.get_log_identifier( request.session )
        if not 'authz_info' in request.session:
            request.session['authz_info'] = { 'authorized': False }
        if request.method == 'POST': # If the form has been submitted...
            if request.session['authz_info']['authorized'] == False:
                return HttpResponseForbidden( '403 / Forbidden' )
            # work_result = common.handleClick( original_status=request.session['current_display_status'], button_action=request.POST['action_button'], item_id=inscrid, log_identifier=log_identifier )
            # common.updateLog( '- in views.viewinscr(); work_result is: %s' % work_result, log_identifier )
            # return HttpResponse( u'<p>INTERRUPT</p>')
            # request.session['click_confirmation_text'] = '%s has been marked as "%s"' % ( inscrid, work_result['new_display_status'] )
            return HttpResponseRedirect( '.' )
        else:    # regular GET
            log.debug( u'in views.viewinscr(); id, %s; GET detected' % log_identifier )
            s = solr.SolrConnection( settings_app.SOLR_URL )
            stateQuery = request.GET.get('qstring')
            log.debug( u'in views.viewinscr(); id, %s; stateQuery, %s' % (log_identifier, stateQuery) )
            statePage = request.GET.get('resultsPage')
            log.debug( u'in views.viewinscr(); id, %s; statePage, %s' % (log_identifier, statePage) )
            qstring = u'inscription_id:%s' % inscrid
            log.debug( u'in views.viewinscr(); id, %s; qstring, %s' % (log_identifier, qstring) )
            try:
                q = s.query(qstring)
                log.debug( u'in views.viewinscr(); id, %s; q.__dict__ (solr query-result) is: %s' % (log_identifier, q.__dict__) )
                # common.updateLog( '- in views.viewinscr(); q try; q.__dict__ (solr query-result) is: %s' % q.__dict__, log_identifier )
            except:
                q = s.query('*:*', **args)
                # common.updateLog( '- in views.viewinscr(); q except; q.__dict__ (solr query-result) is: %s' % q.__dict__, log_identifier )
            ## add the current display_status to the session
            current_display_status = u'init'
            if int( q.numFound ) > 0:
                current_display_status = q.results[0]['display_status']
                request.session['current_display_status'] = current_display_status
            bibs = common.fetchBiblio( q.results, 'bibl')    # 2012-03-14, changed from fetchBiblio(q, '...') for easier testing
            bibDip = common.fetchBiblio( q.results, 'biblDiplomatic')
            bibTsc = common.fetchBiblio( q.results, 'biblTranscription')
            bibTrn = common.fetchBiblio( q.results, 'biblTranslation')
            if request.is_ajax():
                context = {'inscription': q, 'biblios':bibs, 'bibDip' : bibDip, 'bibTsc' : bibTsc, 'bibTrn' : bibTrn,    'biblioFull': False}
                # common.updateLog( '- in views.viewinscr(); is ajax; context is: %s' % context, log_identifier )
                return_str = ajax_snippet.render_block_to_string( 'iip_search_templates/viewinscr.html', 'viewinscr', context )
                return HttpResponse(return_str)
            else:
                chosen_display_status = current_display_status
                temp_context = {
                    'inscription': q,
                    'biblios':bibs,
                    'bibDip' : bibDip,
                    'bibTsc' : bibTsc,
                    'bibTrn' : bibTrn,
                    'biblioFull': True,
                    'chosen_display_status': chosen_display_status,
                    'inscription_id': inscrid,
                    'session_authz_info': request.session['authz_info'], }
                # return render_to_response( 'iip_search_templates/viewinscr.html', temp_context )
                return render( request, u'iip_search_templates/viewinscr.html', temp_context )
    except Exception as e:
        log.error( u'in views.viewinscr(); id, %s; exception, %s' % (log_identifier, unicode(repr(e))) )
        # message = common.makeErrorString()
        # todo: update log
        return HttpResponse( 'oops; unhandled error: %s' % unicode(repr(e)), mimetype='text/javascript' )
        # return HttpResponse( 'unhandled problem; see logs' )
    # end def viewinscr()


## testing ##

def hello( request ):
    """ Testing url handoff. """
    log.debug( u'hello() starting' )
    log.info( u'about to return' )
    return HttpResponse( u'HELLO_WORLD!' )
