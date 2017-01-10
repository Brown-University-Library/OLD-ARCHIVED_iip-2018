# -*- coding: utf-8 -*-

import json, logging, pprint
import redis, rq, solr
from .models import StaticPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, render_to_response
from iip_search_app import common, models, settings_app
from iip_search_app import forms
from iip_search_app.utils import ajax_snippet

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout


log = logging.getLogger(__name__)
q = rq.Queue( u'iip', connection=redis.Redis() )


## search and results ##

def iip_results_z( request ):
    """ Handles /search_zotero/ GET, POST, and ajax-GET. """
    log_id = common.get_log_identifier( request.session )
    log.info( u'in iip_results_z(); id, %s; starting' % log_id )
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    if request.method == u'POST': # form has been submitted by user
        log.debug( 'POST, search-form was submitted by user' )
        request.encoding = u'utf-8'
        form = forms.SearchForm(request.POST)
        if not form.is_valid():
            return HttpResponseRedirect( u'%s://%s%s?q=*:*' % (request.META[u'wsgi.url_scheme'], request.get_host(), reverse(u'results_url')) )
        qstring = form.generateSolrQuery()
        # e.g. http://library.brown.edu/cds/projects/iip/results?q=*:*
        redirect_url = u'%s://%s%s?q=%s' % (request.META[u'wsgi.url_scheme'], request.get_host(), reverse(u'results_url'), qstring)

        return HttpResponseRedirect( redirect_url )
    if request.method == u'GET' and request.GET.get(u'q', None):
        log.debug( 'GET, show search-form' )
        return render( request, u'iip_search_templates/base_zotero.html', _get_POST_context(request, log_id) )
    elif request.is_ajax():  # user has requested another page, a facet, etc.
        log.debug( 'request.is_axax() is True' )
        return HttpResponse( _get_ajax_unistring(request) )
    else:  # regular GET
        return render( request, u'iip_search_templates/search_form_zotero.html', _get_GET_context(request, log_id) )

def _get_POST_context( request, log_id ):
    """ Returns correct context for POST.
        Called by iip_results() """
    log.debug( '_get_POST_context() starting' )
    request.encoding = u'utf-8'

    form = forms.SearchForm( request.POST )  # form bound to the POST data

    qstring_provided = None
    if request.method == u'GET':
        qstring_provided = request.GET.get("q", None)

    if form.is_valid() or qstring_provided:
        initial_qstring = ""
        if qstring_provided:
            initial_qstring = qstring_provided
        else:
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
    log.debug( '_get_GET_context() starting' )
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    # form = SearchForm()  # an unbound form
    form = forms.SearchForm()  # an unbound form
    log.debug( 'form, `%s`' % repr(form) )
    # place_field_object = form.fields['place']
    # place_field_object.choices = [(item, item) for item in sorted( common.facetResults('placeMenu').keys()) if item]
    # form.fields['place'] = place_field_object
    context = {
        u'form': form,
        u'session_authz_info': request.session[u'authz_info'],
        u'settings_app': settings_app,
        u'admin_links': common.make_admin_links( session_authz_dict=request.session[u'authz_info'], url_host=request.get_host(), log_id=log_id )
        }
    log.debug( u'in views._get_GET_context(); context, %s' % context )
    return context


## view inscription ##

def viewinscr_zotero(request, inscrid):
    """ Handles view-inscription GET with new Javascript and Zotero bibliography. """
    log_id = _setup_viewinscr( request )
    log.info( u'in viewinscr(); id, %s; starting' % log_id )
    if request.method == u'POST':  # TODO: call subfunction after getting approval working again
        return _handle_viewinscr_POST( request, inscrid, log_id )
    else:  # GET
        ( q, z_bibids, specific_sources, current_display_status, view_xml_url, current_url ) = _z_prepare_viewinscr_get_data( request, inscrid )
        if request.is_ajax():
            return_response = _z_prepare_viewinscr_ajax_get_response( q, z_bibids, specific_sources, view_xml_url )
        else:
            return_response = _z_prepare_viewinscr_plain_get_response( q, z_bibids, specific_sources, current_display_status, inscrid, request, view_xml_url, current_url, log_id )
        return return_response

# Prepare an inscription using zotero rather than biblio
def _z_prepare_viewinscr_get_data (request, inscrid):
    """ Prepares data for regular or ajax GET.
            Returns a tuple of vars.
        Called by viewinscr(). """
    log.debug( u'in _z_prepare_viewinscr_get_data(); starting' )
    log_id = common.get_log_identifier( request.session )
    q = _call_viewinsc_solr( inscrid )  # The results of the solr query to find the inscription. q.results is list of dictionaries of values.
    current_display_status = _update_viewinscr_display_status( request, q )
    z_bibids_initial = [x.replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", "") for x in q.results[0]['bibl']]
    z_bibids = {}
    for entry in z_bibids_initial:
        bibid, ntype, n = entry.split("|")
        if(not bibid in z_bibids):
            z_bibids[bibid] = []
        if(not (ntype, n) in z_bibids[bibid]):
            z_bibids[bibid].append((ntype, n))
    specific_sources = dict()
    specific_sources['transcription'] = q.results[0]['biblTranscription'][0] if 'biblTranscription' in q.results[0] else ""
    specific_sources['translation'] = q.results[0]['biblTranslation'][0] if 'biblTranslation' in q.results[0] else ""
    specific_sources['diplomatic'] = q.results[0]['biblDiplomatic'][0] if 'biblDiplomatic' in q.results[0] else ""

    view_xml_url = u'%s://%s%s' % (  request.META[u'wsgi.url_scheme'],  request.get_host(),  reverse(u'xml_url', kwargs={u'inscription_id':inscrid})  )
    current_url = u'%s://%s%s' % (  request.META[u'wsgi.url_scheme'],  request.get_host(),  reverse(u'inscription_url_zotero', kwargs={u'inscrid':inscrid})  )
    return ( q, z_bibids, specific_sources, current_display_status, view_xml_url, current_url )

def _setup_viewinscr( request ):
    """ Takes request;
            updates session with authz_info and log_id;
            returns log_id.
        Called by viewinscr() """
    log.debug( u'in _setup_viewinscr(); starting' )
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    log_id = common.get_log_identifier( request.session )
    return log_id

def _handle_viewinscr_POST( request, inscrid, log_id ):
    """ Handles view-inscription POST.
        Returns a response object.
        Called by viewinscr(). """
    log.debug( u'in _handle_viewinscr_POST(); starting' )
    if request.session['authz_info']['authorized'] == False:
        return_response = HttpResponseForbidden( '403 / Forbidden' )
    query_url=u'%s/select/' % settings_app.SOLR_URL
    work_result = common.update_display_status(
        button_action=request.POST['action_button'],
        item_id=inscrid,
        query_url=query_url,
        update_url=settings_app.SOLR_URL,
        log_id=log_id )
    request.session['click_confirmation_text'] = '%s has been marked as "%s"' % ( inscrid, work_result['new_display_status'] )

    # return_response = HttpResponseRedirect( '.' )
    redirect_url = u'%s://%s%s' % (  request.META[u'wsgi.url_scheme'],  request.get_host(),  reverse(u'inscription_url_zotero', kwargs={u'inscrid':inscrid})  )
    log.debug( u'in _handle_viewinscr_POST(); redirect_url, `%s`' % redirect_url )
    return_response = HttpResponseRedirect( redirect_url )

    return return_response

def _prepare_viewinscr_get_data( request, inscrid ):
    """ Prepares data for regular or ajax GET.
            Returns a tuple of vars.
        Called by viewinscr(). """
    log.debug( u'in _prepare_viewinscr_get_data(); starting' )
    log_id = common.get_log_identifier( request.session )
    q = _call_viewinsc_solr( inscrid )
    current_display_status = _update_viewinscr_display_status( request, q )
    ( bibs, bibDip, bibTsc, bibTrn ) = _get_bib_data( q.results )
    view_xml_url = u'%s://%s%s' % (  request.META[u'wsgi.url_scheme'],  request.get_host(),  reverse(u'xml_url', kwargs={u'inscription_id':inscrid})  )
    current_url = u'%s://%s%s' % (  request.META[u'wsgi.url_scheme'],  request.get_host(),  reverse(u'inscription_url_zotero', kwargs={u'inscrid':inscrid})  )
    return ( q, bibs, bibDip, bibTsc, bibTrn, current_display_status, view_xml_url, current_url )

def _call_viewinsc_solr( inscription_id ):
    """ Hits solr with inscription-id.
            Returns a solrpy query-object.
        Called by _prepare_viewinscr_get_data(). """
    s = solr.SolrConnection( settings_app.SOLR_URL )
    qstring = u'inscription_id:%s' % inscription_id
    try:
        q = s.query(qstring)
    except:
        q = s.query('*:*', **args)
    return q

def _update_viewinscr_display_status( request, q ):
    """ Takes request and solrypy query object.
            Updates session  display-status.
            Returns current display-status.
        Called by _prepare_viewinscr_get_data(). """
    current_display_status = u'init'
    if int( q.numFound ) > 0:
        current_display_status = q.results[0]['display_status']
        request.session['current_display_status'] = current_display_status
    return current_display_status

def _get_bib_data( q_results ):
    """ Takes solrpy query-object results.
            Calls bib lookups.
            Returns tuple of lookup data.
        Called by _prepare_viewinscr_get_data().
        TODO: move into models or common. """
    # log.debug( u'in _get_bib_data(); q_results, %s' % pprint.pformat(q_results) )
    bibs = common.fetchBiblio( q_results, 'bibl')
    bibDip = common.fetchBiblio( q_results, 'biblDiplomatic')
    bibTsc = common.fetchBiblio( q_results, 'biblTranscription')
    bibTrn = common.fetchBiblio( q_results, 'biblTranslation')
    return_tuple = ( bibs, bibDip, bibTsc, bibTrn )
    # log.debug( u'in _get_bib_data(); return_tuple, %s' % pprint.pformat(return_tuple) )
    return return_tuple

def _prepare_viewinscr_ajax_get_response( q, bibs, bibDip, bibTsc, bibTrn, view_xml_url ):
    """ Returns view-inscription response-object for ajax GET.
        Called by viewinscr() """
    log.debug( u'in _prepare_viewinscr_ajax_get_response(); starting' )
    context = {
        'inscription': q,
        'biblios':bibs,
        'bibDip' : bibDip,
        'bibTsc' : bibTsc,
        'bibTrn' : bibTrn,
        'biblioFull': False,
        'view_xml_url': view_xml_url }
    return_str = ajax_snippet.render_block_to_string( 'iip_search_templates/viewinscr.html', 'viewinscr', context )
    return_response = HttpResponse( return_str )
    return return_response

def _prepare_viewinscr_plain_get_response( q, bibs, bibDip, bibTsc, bibTrn, current_display_status, inscrid, request, view_xml_url, current_url, log_id ):
    """ Returns view-inscription response-object for regular GET.
        Called by viewinscr() """
    log.debug( u'in _prepare_viewinscr_plain_get_response(); starting' )
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
        'admin_links': common.make_admin_links( session_authz_dict=request.session[u'authz_info'], url_host=request.get_host(), log_id=log_id ),
        'view_xml_url': view_xml_url,
        'current_url': current_url
        }
    # log.debug( u'in _prepare_viewinscr_plain_get_response(); context, %s' % pprint.pformat(context) )
    return_response = render( request, u'iip_search_templates/viewinscr.html', context )
    return return_response

def _z_prepare_viewinscr_ajax_get_response( q, z_bibids, specific_sources, view_xml_url ):
    """ Returns view-inscription response-object for ajax GET.
        Called by viewinscr() """
    log.debug( u'in _prepare_viewinscr_ajax_get_response(); starting' )
    context = {
        'inscription': q,
        'z_ids': z_bibids,
        'biblDiplomatic' : specific_sources['diplomatic'].replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", ""),
        'biblTranscription' : specific_sources['transcription'].replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", ""),
        'biblTranslation' : specific_sources['translation'].replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", ""),
        'biblioFull': False,
        'view_xml_url': view_xml_url }
    return_str = ajax_snippet.render_block_to_string( 'iip_search_templates/viewinscr_zotero.html', 'viewinscr', context )
    return_response = HttpResponse( return_str )
    return return_response

def _z_prepare_viewinscr_plain_get_response( q, z_bibids, specific_sources, current_display_status, inscrid, request, view_xml_url, current_url, log_id ):
    """ Returns view-inscription response-object for regular GET.
        Called by viewinscr() """
    log.debug( u'in _prepare_viewinscr_plain_get_response(); starting' )
    context = {
        'inscription': q,
        'z_ids': z_bibids,
        'biblDiplomatic' : specific_sources['diplomatic'].replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", ""),
        'biblTranscription' : specific_sources['transcription'].replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", ""),
        'biblTranslation' : specific_sources['translation'].replace(".xml", "").replace("bibl=", "").replace("nType=", "").replace("n=", ""),
        'biblioFull': True,
        'chosen_display_status': current_display_status,
        'inscription_id': inscrid,
        'session_authz_info': request.session['authz_info'],
        'admin_links': common.make_admin_links( session_authz_dict=request.session[u'authz_info'], url_host=request.get_host(), log_id=log_id ),
        'view_xml_url': view_xml_url,
        'current_url': current_url,
        }
    # log.debug( u'in _prepare_viewinscr_plain_get_response(); context, %s' % pprint.pformat(context) )
    return_response = render( request, u'iip_search_templates/viewinscr_zotero.html', context )
    return return_response

## api ##

def api_wrapper( request ):
    old_params = dict(request.GET)
    params = dict([(x.replace('.', '_'), old_params[x] if len(old_params[x]) > 1 else old_params[x][0]) for x in old_params])
    params['wt'] = 'json'
    if(params['q']): params['q'] += " AND display_status:approved"
    s = solr.SolrConnection( settings_app.SOLR_URL )

    r = s.raw_query(**params)

    return HttpResponse( str(r), content_type="application/json" )

## login ##

def login( request ):
    """ Takes shib-eppn or 'dev_auth_hack' parameter (if enabled for non-shibbolized development) and checks it agains settings list of LEGIT_ADMINS. """
    ## init
    log_id = common.get_log_identifier( request.session )
    log.info( u'in login(); id, %s; starting' % log_id )
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
    log.info( u'in logout(); starting' )
    request.session[u'authz_info'] = { u'authorized': False }
    django_logout( request )
    if u'next' in request.GET:
        redirect_url = request.GET[u'next']
    else:
        redirect_url = u'%s://%s%s' % (
            request.META[u'wsgi.url_scheme'], request.get_host(), reverse(u'search_url',) )
    return HttpResponseRedirect( redirect_url )


## process ##  request.session['authz_info'] = { 'authorized': True, 'firstname': request.META['Shibboleth-givenName'] }

def process_new( request ):
    """ Triggers svn-update and processing of all new records. """
    log.info( u'in iip_search_app.views.process_new(); starting' )
    if request.session[u'authz_info'][u'authorized'] == False:
        log.info( u'in iip_search_app.views.process_new(); not authorized, returning Forbidden' )
        return HttpResponseForbidden( '403 / Forbidden' )
    q.enqueue_call( func=u'iip_search_app.models.run_call_svn_update', kwargs = {} )
    return HttpResponse( u'Started processing updated inscriptions.' )

def process_orphans( request ):
    """ Triggers deletion of solr-inscription-ids that do not have corresponding repository ids. """
    log.info( u'in iip_search_app.views.process_orphans(); starting' )
    if request.session[u'authz_info'][u'authorized'] == False:
        log.info( u'in iip_search_app.views.process_orphans(); not authorized, returning Forbidden' )
        return HttpResponseForbidden( '403 / Forbidden' )
    q.enqueue_call( func=u'iip_search_app.models.run_delete_orphans', kwargs = {} )
    return HttpResponse( u'Started processing solr orphan deletion.' )

def process_all( request ):
    """ Returns confirmation-required response. """
    log.info( u'in iip_search_app.views.process_all(); starting' )
    if request.session[u'authz_info'][u'authorized'] == False:
        log.info( u'in iip_search_app.views.process_all(); not authorized, returning Forbidden' )
        return HttpResponseForbidden( '403 / Forbidden' )
    request.session[u'process_all_initiated'] = True
    return HttpResponse( u'Please confirm: in url change `all` to `confirm_all`. This will not change proofreading status.' )

def process_confirm_all( request ):
    """ Triggers processing of all inscriptions. """
    if request.session[u'authz_info'][u'authorized'] == False:
        log.info( u'in iip_search_app.views.process_confirm_all(); not authorized, returning Forbidden' )
        return HttpResponseForbidden( '403 / Forbidden' )
    if request.session.get( u'process_all_initiated', False ) == True:  # if it doesn't exist, create and set to False
        request.session[u'process_all_initiated'] = False
        q.enqueue_call( func=u'iip_search_app.models.run_process_all_files', kwargs = {} )
        return HttpResponse( u'Started processing all inscriptions; all should be complete within an hour.' )
    else:
        return HttpResponse( u'Initial url must be `all`, not `confirm_all`.' )

def process_single( request, inscription_id ):
    """ Triggers, after instruction, processing of given iscription. """
    log.info( u'in iip_search_app.views.process_single(); starting; inscription_id, `%s`' % inscription_id )
    if request.session[u'authz_info'][u'authorized'] == False:
        log.info( u'in iip_search_app.views.process_single(); not authorized, returning Forbidden' )
        return HttpResponseForbidden( '403 / Forbidden' )
    if inscription_id == u'INSCRIPTION_ID':
        return HttpResponse( u'In url above, replace `INSCRIPTION_ID` with id to process, eg `ahma0002`. This will not change proofreading status.' )
    else:
        q.enqueue_call( func=u'iip_search_app.models.run_process_single_file', kwargs = {u'inscription_id': inscription_id} )
        return HttpResponse( u'Started processing inscription-id.' )

def show_recent_errors( request ):
    """ Displays last x entries in the failed queue. """
    log.info( u'in iip_search_app.views.show_recent_errors(); starting' )
    TARGET_QUEUE = u'iip'
    queue_name = u'failed'
    q = rq.Queue( queue_name, connection=redis.Redis() )
    recent_jobs = sorted( q.jobs[-25:], reverse=True )
    dict_list = []
    for job in recent_jobs:
        job_d = {
            u'description': job.description,
            u'datetime': unicode( job.created_at ),
            u'traceback': job.exc_info,
            }
        dict_list.append( job_d )
    output = json.dumps( dict_list, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type = u'application/javascript; charset=utf-8' )


## view_xml ##

def view_xml( request, inscription_id ):
    """ Returns inscription xml. """
    log.info( u'in view_xml(); starting' )
    file_path = u'%s/%s.xml' % ( settings_app.XML_DIR_PATH, inscription_id )
    log.debug( u'in view_xml(); id, %s; file_path' % file_path )
    with open( file_path ) as f:
        xml_utf8 = f.read()
        xml = xml_utf8.decode(u'utf-8')
    return HttpResponse( xml, mimetype=u'text/xml' )


## static pages ##

def info( request, info_id ):
    """ Displays requested static page. """
    info_page = get_object_or_404( StaticPage, slug=info_id )
    context_dct = {
        'html_content': info_page.content,
        'title_header': info_page.title_header,
        'title': info_page.title
        }
    return render( request, u'iip_search_templates/static.html', context_dct )

def edit_info( request ):
    """ If logged in, takes user to static-pages admin. """
    if 'authz_info' not in request.session.keys() or 'authorized' not in request.session[u'authz_info'].keys() or request.session[u'authz_info'][u'authorized'] == False:
        return HttpResponseForbidden( '403 / Forbidden' )
    user = authenticate( username=settings_app.DB_USER, password=settings_app.DB_USER_PASSWORD )
    django_login( request, user )
    url = reverse( 'admin:iip_search_app_staticpage_changelist' )
    return HttpResponseRedirect( url )
