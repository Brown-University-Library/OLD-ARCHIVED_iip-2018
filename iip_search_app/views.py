# -*- coding: utf-8 -*-

from django.http import HttpResponse
from iip_search_app import common
from iip_search_app.forms import SearchForm


def hello( request ):
    """ Testing url handoff. """
    return HttpResponse( u'HELLO_WORLD!' )


def iip_results( request ):
    """ Handles /search/ GET, POST, and ajax-GET. """
    try:
        log_identifier = common.get_log_identifier( request.session )
        if not u'authz_info' in request.session:
            request.session[u'authz_info'] = { u'authorized': False }
        if request.method == u'POST':  # form has been submitted by user
            post_context = _get_POST_context( request )
            return render_to_response( u'base_extend.html', post_context )
        elif request.is_ajax():  # user has requested another page, a facet, etc.
            return_unistring = _get_ajax_unistring( request )
            return HttpResponse( return_unistring )
        else:  # regular GET
            get_context = _get_GET_context( request )
            return render_to_response( u'search_form.html', context )
    except Exception as e:
      # message = common.makeErrorString()
      # todo: update log
      return HttpResponse( 'oops; unhandled error: %s' % unicode(repr(e)), mimetype=u'text/javascript' )
      # return HttpResponse( 'unhandled problem; see logs' )
    # end def iipResults()

def _get_POST_context( request ):
    """ Returns correct context for POST.
        Called by iip_results() """
    request.encoding = u'utf-8'
    form = SearchForm( request.POST ) # form bound to the POST data
    if form.is_valid():
        initial_qstring = form.generateSolrQuery()
        resultsPage = 1
        updated_qstring = common.updateQstring( initial_qstring, request.session['authz_info'], log_identifier )['modified_qstring']
        context = common.paginateRequest( updated_qstring, resultsPage, log_identifier )
        context[u'session_authz_info'] = request.session[u'authz_info']
        return context

def _get_ajax_unistring( request ):
    """ Returns unicode string based on ajax update.
        Called by iip_results() """
    log_identifier = request.session[u'log_identifier']
    initial_qstring = request.GET.get( u'qstring', u'*:*' )
    updated_qstring = common.updateQstring( initial_qstring, request.session[u'authz_info'], log_identifier )[u'modified_qstring']
    resultsPage = int( request.GET[u'resultsPage'] )
    context = paginateRequest( updated_qstring, resultsPage, log_identifier )
    return_str = render_block_to_string(u'base_extend.html', u'content', context)
    return unicode( return_str )

def _get_GET_context( request ):
    """ Returns correct context for GET.
        Called by iip_results() """
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    form = SearchForm()  # an unbound form
    context = {
        u'form': form,
        u'session_authz_info': request.session[u'authz_info'],
        u'settings_app': settings_app }
    return context


