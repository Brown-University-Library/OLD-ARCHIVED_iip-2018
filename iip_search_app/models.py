# -*- coding: utf-8 -*-

import datetime, os, pprint, random, subprocess
import requests


class Processor( object ):
    """ Container for various tasks involved in processing inscription metadata.
        Non-django, plain-python model.
        No dango dependencies, including settings. """

    def __init__( self ):
        """ Settings. """
        self.TEMPFILES_DIR_PATH = unicode( os.environ.get(u'IIP_SEARCH__TEMPFILES_DIR_PATH') )  # for stdout and stderr
        self.VC_XML_URL = unicode( os.environ.get(u'IIP_SEARCH__VC_XML_URL') )  # version control url
        self.XML_DIR_PATH = unicode( os.environ.get(u'IIP_SEARCH__XML_DIR_PATH') )
        self.MUNGER_SCRIPT_DIRECTORY = unicode( os.environ.get(u'IIP_SEARCH__MUNGER_SCRIPT_DIRECTORY') )
        self.MUNGER_SCRIPT_XML_DIRECTORY = unicode( os.environ.get(u'IIP_SEARCH__MUNGER_SCRIPT_XML_DIRECTORY') )
        self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY = unicode( os.environ.get(u'IIP_SEARCH__MUNGER_SCRIPT_MUNGED_XML_DIRECTORY') )

        self.SOLR_DOC_STYLESHEET_PATH = unicode( os.environ.get(u'IIP_SEARCH__SOLR_DOC_STYLESHEET_PATH') )
        self.TRANSFORMER_URL = unicode( os.environ.get(u'IIP_SEARCH__TRANSFORMER_URL') )

    def process_file( self, file_id, current_display_facet=None ):
        """ Takes file_id string.
                Runs svn-export on file,
                Grabs source xml,
                Runs munger,
                Runs xslt to create solr-doc,
                Updates solr-doc display facet,
                Posts to solr.
                Returns processing dict.
            Called by (eventually)
                views.viewinscr() subfunction via logged-in user (current_display_facet passed in),
                update-new-files script (current_display_facet = None),
                update-all-files script (current_display_facet looked up and passed in if available),
                github commit hook (current_display_facet looked up and passed in if available). """
        process_dict = {
            u'a__grab_latest_file': {u'status': u'', u'data': u''},
            u'b__grab_source_xml': {u'status': u'', u'data': u''},
            u'c__run_munger': {u'status': u'', u'data': u''},
            u'd__make_initial_solr_doc': {u'status': u'', u'data': u''},
            u'e__update_display_facet': {u'status': u'', u'data': u''},
            u'f__post_to_solr': {u'status': u'', u'data': u''},
            }
        process_dict[u'a__grab_latest_file'] = self.grab_latest_file(
            file_id )
        process_dict[u'b__grab_source_xml'] = self.grab_original_xml(
            file_id )
        process_dict[u'c__run_munger'] = self.run_munger(
            source_xml=process_dict[u'b__grab_source_xml'][u'data'] )
        process_dict[u'd__make_initial_solr_doc'] = self.make_initial_solr_doc(
            munged_xml=process_dict[u'c__run_munger'][u'data'] )
        process_dict[u'e__update_display_facet'] = self.update_display_facet(
            file_id=file_id, initial_solr_xml=process_dict[u'd__make_initial_solr_doc'][u'data'], current_display_facet=current_display_facet  )
        process_dict[u'f__post_to_solr'] = self.post_to_solr(
            file_id=file_id, updated_solr_xml=process_dict[u'e__update_display_facet'][u'data'] )
        return process_dict

    ## helpers for above ##

    def grab_latest_file( self, file_id ):
        """ Takes file_id string.
                Runs an svn-export.
                Returns output dict.
            Called by process_file().
            Note: no user/pass required; works after manually running svn command once. """
        ## setup
        ( f_stdout, f_stderr, file_url, xml_destination_path, temp_stdout_filepath, temp_stderr_filepath ) = self._setup_grab_files( file_id )
        ## work
        subprocess.call( [u'svn', u'export', u'--force', file_url, xml_destination_path], stdout=f_stdout, stderr=f_stderr )
        ## populate output
        ( f_stdout, f_stderr, var_stdout, var_stderr ) = self._prep_grab_output( f_stdout, f_stderr, temp_stdout_filepath, temp_stderr_filepath )
        ## return
        return_dict = {
            u'stderr': var_stderr, u'stdout': var_stdout,
            u'submitted_file_id': file_id, u'submitted_vc_url': file_url, u'submitted_destination_path': xml_destination_path }
        return return_dict

    def _setup_grab_files( self, file_id ):
        """ Takes file_id string.
                Initializes temp files.
                Returns tuple of vars.
            Called by grab_latest_file() """
        ( temp_stdout_filepath, temp_stderr_filepath ) = ( self._make_temp_filepath(u'stdout_vcs'), self._make_temp_filepath(u'stderr_vcs') )
        f_stdout = open( temp_stdout_filepath, u'w' )
        f_stderr = open( temp_stderr_filepath, u'w' )
        f_stdout.write( u'' )
        f_stderr.write( u'' )
        file_url = u'%s/%s.xml' % ( self.VC_XML_URL, file_id )
        xml_destination_path = u'%s/%s.xml' % ( self.XML_DIR_PATH, file_id )
        return ( f_stdout, f_stderr, file_url, xml_destination_path, temp_stdout_filepath, temp_stderr_filepath )

    def _prep_grab_output( self, f_stdout, f_stderr, temp_stdout_filepath, temp_stderr_filepath ):
        """ Takes file-objects and path strings.
                Closes files, sets return vars, deletes temp files.
                Returns tuple of vars.
            Called by grab_latest_file() """
        f_stdout.close()
        f_stderr.close()
        f_stdout = open( temp_stdout_filepath, u'r' )
        f_stderr = open( temp_stderr_filepath, u'r' )
        var_stdout = f_stdout.readlines()
        var_stderr = f_stderr.readlines()
        f_stdout.close()
        f_stderr.close()
        os.remove( temp_stdout_filepath )
        os.remove( temp_stderr_filepath )
        return ( f_stdout, f_stderr, var_stdout, var_stderr )

    ##

    def _make_temp_filepath( self, prefix ):
        """ Takes prefix string.
                Creates file name based on prefix, date, and random number.
                Returns created file name string.
            Called by _setup_grab_files(), and eventually a munger subfunction. """
        now_string = unicode( datetime.datetime.now() ).replace( u' ', u'_' )
        random_string = random.randint( 1000,9999 )
        filepath = u'%s/%s_%s_%s' % ( self.TEMPFILES_DIR_PATH , prefix, now_string, random_string )
        return filepath

    ##

    def grab_original_xml( self, file_id ):
        """ Takes file_id string.
                Returns xml file in return_dict.
            Called by process_file(). """
        filepath = u'%s/%s.xml' % ( self.XML_DIR_PATH, file_id )
        with open( filepath ) as f:
            xml_utf8 = f.read()
        assert type(xml_utf8) == str, type(xml_utf8)
        xml = xml_utf8.decode( u'utf-8' )
        return_dict = {
            u'submitted_file_id': file_id,
            u'filepath': filepath,
            u'xml': xml
            }
        return return_dict

    ##

    def run_munger( self, source_xml ):
        """ Takes source xml unicode string.
                Applies perl munger.
                Returns processed xml.
            Called by process_file(). """
        assert type(source_xml) == unicode, type(source_xml)
        assert type(self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY) == unicode, type(self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY)
        assert type(self.MUNGER_SCRIPT_XML_DIRECTORY) == unicode, type(self.MUNGER_SCRIPT_XML_DIRECTORY)
        assert type(self.TEMPFILES_DIR_PATH) == unicode, type(self.TEMPFILES_DIR_PATH)
        ## save file w/identifier as part of name
        file_name_root = u'FILE_%s' % random.randint(1000,9999)    # need this root part later
        file_name = u'%s.xml' % file_name_root
        filepath = u'%s/%s' % ( self.MUNGER_SCRIPT_XML_DIRECTORY, file_name )
        f = open( filepath, u'w' )
        f.write( source_xml.encode(u'utf-8') )
        f.close()
        ## call script (called script automatically saves file in various processing and a final directory)
        current_working_directory = os.getcwd()
        os.chdir( self.MUNGER_SCRIPT_DIRECTORY )
        var = u'1'    # days; required by script; tells script to process all files updated in last day
        command_list = [ u'./strip.pl', var ]
        ## open temp files
        ( temp_stdout_filepath, temp_stderr_filepath ) = ( self._make_temp_filepath(u'stdout_munger'), self._make_temp_filepath(u'stderr_munger') )
        f_stdout = open( temp_stdout_filepath, u'w' )
        f_stderr = open( temp_stderr_filepath, u'w' )
        f_stdout.write( u'' )
        f_stderr.write( u'' )
        ## run command
        subprocess.call( command_list, stdout=f_stdout, stderr=f_stderr )
        ## populate output
        f_stdout.close()
        f_stderr.close()
        ## read output file into string
        filepath = u'%s/%s' % ( self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY, file_name )
        f = open( filepath )
        munged_xml_string = f.read()
        assert type(munged_xml_string) == str, type(munged_xml_string)
        munged_xml_ustring = munged_xml_string.decode(u'utf-8')
        f.close()
        ## cleanup & return
        files_to_delete = [
            u'%s/%s' % ( self.MUNGER_SCRIPT_XML_DIRECTORY, file_name ),
            u'%s/%s' % ( self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY, file_name ),
            u'%s/Cloned/%s.cloned.xml' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
            u'%s/Copied/%s' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name ),
            u'%s/Decomposed/%s.cloned.decomposed.xml' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
            u'%s/Final/%s' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name ),
            u'%s/Stripped/%s.cloned.decomposed.stripped.xml' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
            ]
        # print u'files_to_delete...'; pprint.pprint( files_to_delete )
        for entry in files_to_delete:
            assert os.path.exists(entry) == True, os.path.exists(entry)
            os.remove( entry )
            assert os.path.exists(entry) == False, os.path.exists(entry)
        os.chdir( current_working_directory )    # otherwise may affect other scripts
        ## return
        return {
            u'source_xml': source_xml,
            u'munged_xml': munged_xml_ustring
            }
        # end def runMunger()

    ##

    def make_initial_solr_doc( self, munged_xml ):
        '''
        Applies the iip munged-data-to-solrdoc stylesheet to create the solrdoc.
        '''
        try:
            import requests
            assert type(settings_app.SOLR_DOC_STYLESHEET_PATH) == unicode, type(settings_app.SOLR_DOC_STYLESHEET_PATH)
            assert type(settings_app.TRANSFORMER_URL) == unicode, type(settings_app.TRANSFORMER_URL)
            assert type(self.xml_munged) == unicode, type(self.xml_munged)
        iip_solrdoc_string = 'init'
        ## get stylesheet
            f = open( settings_app.SOLR_DOC_STYLESHEET_PATH )
        stylesheet_string = f.read()
        f.close()
        assert type(stylesheet_string) == str, type(stylesheet_string)
        stylesheet_ustring = stylesheet_string.decode(u'utf-8')
        ## hit the post xslt transformer
            url = settings_app.TRANSFORMER_URL
        payload = {
                u'source_string': self.xml_munged,
            u'stylesheet_string': stylesheet_ustring }
        headers = { u'content-type': u'text/xml; charset=utf-8' }
        r = requests.post( url, data=payload, headers=headers )
            self.xml_xslted = r.content.decode(u'utf-8')
            self.save()
        except:
            '''
            For reference, one possible return on error:
            {u'solr_doc_string': u'FAILURE', u'message': "error-type - <class 'urllib2.URLError'>; error-message - <urlopen error timed out>; line-number - 249"}
            '''
            message = common.makeErrorString()
            self.problem_log = smart_unicode( message )
            self.save()

    ##

    def update_display_facet( self, file_id, initial_solr_xml, current_display_facet ):
        '''
        - Purpose: Takes solr doc and adds a 'display_status' field.
        TODO: POSSIBLE NEW-DISPLAY-FACET
        '''
        try:
            import StringIO, sys
            from lxml import etree
            assert type(self.xml_xslted) == unicode, type(self.xml_xslted)
            doc = etree.fromstring( self.xml_xslted.encode(u'utf-8'))    # can't take unicode string due to xml file's encoding declaration
            node = doc.xpath( u'//doc' )[0]
            new_field = etree.SubElement( node, u'field' )
            new_field.attrib[u'name'] = u'display_status'
            new_field.text = u'to_approve'
            xml_string = etree.tostring( doc, encoding=u'UTF-8', xml_declaration=True, pretty_print=False )
            assert type(xml_string) == str, type(xml_string)
            self.xml_statusified = xml_string.decode(u'utf-8')
            self.save()
        except:
            message = common.makeErrorString()
            self.problem_log = smart_unicode( message )
            self.save()

    ##

    def updateSolr( self, file_id, updated_solr_xml ):
        '''
        - Purpose: posts solr-doc to solr & saves response.
        '''
        try:
            import requests
            assert type(settings_app.SOLR_URL) == unicode, type(settings_app.SOLR_URL)
            assert type(self.xml_statusified) == unicode, type(xml_statusified)
            update_url = u'%s/update/?commit=true' % settings_app.SOLR_URL
            headers = { 'content-type': 'text/xml; charset=utf-8' }    # from common.updateSolr() testing, non-unicode-string posts were bullet-proof
            r = requests.post(
                update_url.encode(u'utf-8'),
                headers=headers,
                data=self.xml_statusified.encode(u'utf-8') )
            self.solrization_response = r.content.decode(u'utf-8')
            self.save()
        except:
            message = common.makeErrorString()
            self.problem_log = smart_unicode( message )
            self.save()

    # def grabInscriptionId( self ):
    #     try:
    #         assert type(self.filepath) == unicode, type(filepath)
    #         segment = self.filepath.split( u'/' )[-1]
    #         if not segment[-4:] == u'.xml':
    #             self.inscription_id = u'FAILURE'
    #         else:
    #             self.inscription_id = segment[0:-4]
    #     except Exception, e:
    #         self.problem_log = smart_unicode(e)

    ## end class Processor()
