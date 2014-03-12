# -*- coding: utf-8 -*-

import logging
import solr
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
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
        return render( request, u'iip_search_templates/base_extend.html', _get_POST_context(request, log_id) )
    elif request.is_ajax():  # user has requested another page, a facet, etc.
        return HttpResponse( _get_ajax_unistring(request) )
    else:  # regular GET
        return render( request, u'iip_search_templates/search_form.html', _get_GET_context(request, log_id) )

def _get_POST_context( request, log_id ):
    """ Returns correct context for POST.
        Called by iip_results() """
    request.encoding = u'utf-8'
    form = SearchForm( request.POST ) # form bound to the POST data
    if form.is_valid():
        initial_qstring = form.generateSolrQuery()
        resultsPage = 1
        updated_qstring = common.updateQstring(
            initial_qstring=initial_qstring, session_authz_dict=request.session['authz_info'], log_id=common.get_log_identifier(request.session) )['modified_qstring']
        context = common.paginateRequest( qstring=updated_qstring, resultsPage=resultsPage, log_id=common.get_log_identifier(request.session) )
        context[u'session_authz_info'] = request.session[u'authz_info']
        context[u'admin_links'] = common.make_admin_links( session_authz_dict=request.session[u'authz_info'], url_host=request.get_host(), log_id=log_id )
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

def _get_GET_context( request, log_id ):
    """ Returns correct context for GET.
        Called by iip_results() """
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    form = SearchForm()  # an unbound form
    context = {
        u'form': form,
        u'session_authz_info': request.session[u'authz_info'],
        u'settings_app': settings_app,
        u'admin_links': common.make_admin_links( session_authz_dict=request.session[u'authz_info'], url_host=request.get_host(), log_id=log_id )
        }
    log.debug( u'in views._get_GET_context(); context, %s' % context )
    return context


## view inscription ##

def viewinscr( request, inscrid ):
    """ Handles view-inscription GET, ajax-GET, and approval-update POST. """
    log_id = _setup_viewinscr( request )
    if request.method == u'POST':  # TODO: call subfunction after getting approval working again
        return _handle_viewinscr_POST( request )
    else:  # GET
        ( q, bibs, bibDip, bibTsc, bibTrn, current_display_status ) = _prepare_viewinscr_get_data( request, inscrid )
        if request.is_ajax():
            return_response = _prepare_viewinscr_ajax_get_response( q, bibs, bibDip, bibTsc, bibTrn )
        else:
            return_response = _prepare_viewinscr_plain_get_response( q, bibs, bibDip, bibTsc, bibTrn, current_display_status, inscrid, request, log_id )
        return return_response

def _setup_viewinscr( request ):
    """ Takes request;
            updates session with authz_info and log_id;
            returns log_id.
        Called by viewinscr() """
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    log_id = common.get_log_identifier( request.session )
    return log_id

def _handle_viewinscr_POST( request ):
    """ Handles view-inscription POST.
        Returns a response object.
        Called by viewinscr(). """
    if request.session['authz_info']['authorized'] == False:
        return_response = HttpResponseForbidden( '403 / Forbidden' )
    # work_result = common.handleClick( original_status=request.session['current_display_status'], button_action=request.POST['action_button'], item_id=inscrid, log_id=log_id )
    # common.updateLog( '- in views.viewinscr(); work_result is: %s' % work_result, log_id )
    # return HttpResponse( u'<p>INTERRUPT</p>')
    # request.session['click_confirmation_text'] = '%s has been marked as "%s"' % ( inscrid, work_result['new_display_status'] )
    return_response = HttpResponseRedirect( '.' )
    return return_response

def _prepare_viewinscr_get_data( request, inscrid ):
    """ Prepares data for regular or ajax GET.
        Returns a tuple of vars.
        Called by viewinscr(). """
    log_id = common.get_log_identifier( request.session )
    s = solr.SolrConnection( settings_app.SOLR_URL )
    stateQuery = request.GET.get('qstring')
    statePage = request.GET.get('resultsPage')
    qstring = u'inscription_id:%s' % inscrid
    try:
        q = s.query(qstring)
    except:
        q = s.query('*:*', **args)
    ## add the current display_status to the session
    current_display_status = u'init'
    if int( q.numFound ) > 0:
        current_display_status = q.results[0]['display_status']
        request.session['current_display_status'] = current_display_status
    bibs = common.fetchBiblio( q.results, 'bibl')    # 2012-03-14, changed from fetchBiblio(q, '...') for easier testing
    bibDip = common.fetchBiblio( q.results, 'biblDiplomatic')
    bibTsc = common.fetchBiblio( q.results, 'biblTranscription')
    bibTrn = common.fetchBiblio( q.results, 'biblTranslation')
    return ( q, bibs, bibDip, bibTsc, bibTrn, current_display_status )

def _prepare_viewinscr_ajax_get_response( q, bibs, bibDip, bibTsc, bibTrn ):
    """ Returns view-inscription response-object for ajax GET.
        Called by viewinscr() """
    context = {
        'inscription': q,
        'biblios':bibs,
        'bibDip' : bibDip,
        'bibTsc' : bibTsc,
        'bibTrn' : bibTrn,
        'biblioFull': False }
    return_str = ajax_snippet.render_block_to_string( 'iip_search_templates/viewinscr.html', 'viewinscr', context )
    return_response = HttpResponse( return_str )
    return return_response

def _prepare_viewinscr_plain_get_response( q, bibs, bibDip, bibTsc, bibTrn, current_display_status, inscrid, request, log_id ):
    """ Returns view-inscription response-object for regular GET.
        Called by viewinscr() """
    context = {
        'inscription': q,
        'biblios':bibs,
        'bibDip' : bibDip,
        'bibTsc' : bibTsc,
        'bibTrn' : bibTrn,
        'biblioFull': True,
        'chosen_display_status': current_display_status,
        'inscription_id': inscrid,
        'session_authz_info': request.session['authz_info'],
        'admin_links': common.make_admin_links( session_authz_dict=request.session[u'authz_info'], url_host=request.get_host(), log_id=log_id )
        }
    return_response = render( request, u'iip_search_templates/viewinscr.html', context )
    return return_response


## login ##

def login( request ):
    """ Takes shib-eppn or 'dev_auth_hack' parameter (if enabled for non-shibbolized development) and checks it agains settings list of LEGIT_ADMINS. """
    ## init
    log_id = common.get_log_identifier( request.session )
    log.info( u'in views.login(); id, %s; starting' % log_id )
    request.session['authz_info'] = { 'authorized': False }
    ## checks
    if _check_shib( request, log_id ) == False:
        _check_dev_auth_hack( request, log_id )
    ## response
    response = _make_response( request, log_id )
    return response

def _check_shib( request, log_id ):
    """ Takes request;
            examines it for shib info and updates request.session if necessary;
            returns True or False.
        Called by login() """
    log.info( u'in views._check_shib(); id, %s; starting' % log_id )
    return_val = False
    if 'Shibboleth-eppn' in request.META:
        if request.META['Shibboleth-eppn'] in settings_app.LEGIT_ADMINS:  # authorization passed
          request.session['authz_info'] = { 'authorized': True, 'firstname': request.META['Shibboleth-givenName'] }
          return_val = True
    return return_val

def _check_dev_auth_hack( request, log_id ):
    """ Takes request;
            examines it, and settings, for dev_auth_hack and updates request.session if necessary.
        Called by login() """
    log.info( u'in views._check_dev_auth_hack(); id, %s; starting' % log_id )
    if 'dev_auth_hack' in request.GET and settings_app.DEV_AUTH_HACK == 'enabled':
        log.info( u'in views._check_dev_auth_hack(); id, %s; dev_auth_hack exists and is enabled' % log_id )
        if request.GET['dev_auth_hack'] in settings_app.LEGIT_ADMINS:
            log.info( u'in views._check_dev_auth_hack(); id, %s; param is a legit-admin' % log_id )
            request.session['authz_info'] = { 'authorized': True, 'firstname': request.GET['dev_auth_hack'] }
            log.info( u'in views._check_dev_auth_hack(); id, %s; session authorization to True' % log_id )
    return

def _make_response( request, log_id ):
    """ Takes request;
            examines session['authz_info'];
            returns a response object to caller.
        Called by login(). """
    log.info( u'in views._make_response(); id, %s; starting' % log_id )
    if request.session['authz_info']['authorized'] == True:
        if 'next' in request.GET:
          response = HttpResponseRedirect( request.GET['next'] )
        else:
            redirect_url = u'%s://%s%s' % (
                request.META[u'wsgi.url_scheme'], request.get_host(), reverse(u'search_url',) )
        response = HttpResponseRedirect( redirect_url )
    else:
        response = HttpResponseForbidden( '403 / Forbidden; unauthorized user' )
    return response


## logout ##

def logout( request ):
    """ Removes session-based authentication. """
    request.session[u'authz_info'] = { u'authorized': False }
    if u'next' in request.GET:
        redirect_url = request.GET[u'next']
    else:
        redirect_url = u'%s://%s%s' % (
            request.META[u'wsgi.url_scheme'], request.get_host(), reverse(u'search_url',) )
    return HttpResponseRedirect( redirect_url )


## reprocess ##

def reprocess( request, inscription_id ):
    """ Initiated from view-inscription page.
        Takes inscription_id and display_status.
            Checks authN/Z; executes reprocess of current inscription.
            Returns current view-inscription page.
        """
    return HttpResponse( u'coming' )


## testing ##

def hello( request ):
    """ Testing url handoff. """
    log.debug( u'hello() starting' )
    log.info( u'about to return' )
    return HttpResponse( u'HELLO_WORLD!' )
