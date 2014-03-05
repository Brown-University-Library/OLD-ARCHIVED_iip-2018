# -*- coding: utf-8 -*-


class Processor( object ):
    """ Container for various tasks involved in processing inscription metadata.
        (non-django, plain-python model) """

    def process_file( self, file_id, current_display_facet=None ):
        """ Takes file_id string;
                Runs svn-export on file,
                Grabs source xml,
                Runs munger,
                Runs xslt to create solr-doc,
                Updates solr-doc display facet,
                Posts to solr;
            Returns processing dict;
            Called by (eventually)
                views.viewinscr() subfunction via logged-in user (current_display_facet passed in),
                update-new-files script (current_display_facet = None),
                update-all-files script (current_display_facet looked up and passed in if available),
                github commit hook (current_display_facet looked up and passed in if available) """
        process_dict = {
            u'a__svn_export': {u'status': u'', u'data': u''},
            u'b__grab_source_xml': {u'status': u'', u'data': u''},
            u'c__run_munger': {u'status': u'', u'data': u''},
            u'd__make_initial_solr_doc': {u'status': u'', u'data': u''},
            u'e__update_display_facet': {u'status': u'', u'data': u''},
            u'f__post_to_solr': {u'status': u'', u'data': u''},
            }
        process_dict[u'a__svn_export'] = self.run_svn_export(
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

    def run_svn_export( self, file_id ):
        '''
        - Purpose: to execute an svn export command on given svn-repository file and return output.
        - Called by: script__detect_new_files
        '''
        try:
            import subprocess
            updateLog( '- in common.runSvnExport(); file_url is: %s; destination_path is: %s' % ( file_url, destination_path ), log_identifier )
            ## open temp files
            f_stdout = open( settings_app.SCRIPT_TEMP_STDOUT_PATH, 'w' )
            f_stderr = open( settings_app.SCRIPT_TEMP_STDERR_PATH, 'w' )
            f_stdout.write( '' )
            f_stderr.write( '' )
            ## make call
            subprocess.call( ['svn', 'export', file_url, destination_path], stdout=f_stdout, stderr=f_stderr )
            ## populate output
            f_stdout.close()
            f_stderr.close()
            f_stdout = open( settings_app.SCRIPT_TEMP_STDOUT_PATH, 'r' )
            f_stderr = open( settings_app.SCRIPT_TEMP_STDERR_PATH, 'r' )
            svn_stdout = f_stdout.readlines()
            svn_stderr = f_stderr.readlines()
            f_stdout.close()
            f_stderr.close()
            return_dict = {
                'stderr': svn_stderr,
                'stdout': svn_stdout,
                'submitted_file_url': file_url,
                'submitted_destination_path': destination_path }
            updateLog( '- in common.runSvnExport(); return_dict is: %s' % return_dict, log_identifier )
            return return_dict
        except Exception, e:
            # print '- simple e is: %s' % e
            message = makeErrorString()
            updateLog( '- in common.runSvnExport(); error: %s' % message, log_identifier, message_importance='high' )
            return { 'error_message': message }
        # end def runSvnExport()

    def grab_original_xml( self, file_id ):
        try:
            assert type(self.filepath) == unicode, type(self.filepath)
            f = open( self.filepath )
            xml_string = f.read()
            f.close()
            assert type(xml_string) == str, type(xml)
            xml_ustring = xml_string.decode( u'utf-8' )
            self.xml_original = xml_ustring
            self.save()
        except:
            message = common.makeErrorString()
            self.problem_log = smart_unicode( message )
            self.save()

    def run_munger( self, source_xml ):
        try:
            import random, os, subprocess
            assert type(settings_app.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY) == unicode, type(settings_app.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY)
            assert type(settings_app.MUNGER_SCRIPT_XML_DIRECTORY) == unicode, type(settings_app.MUNGER_SCRIPT_XML_DIRECTORY)
            assert type(settings_app.SCRIPT_TEMP_STDERR_PATH) == unicode, type(settings_app.SCRIPT_TEMP_STDERR_PATH)
            assert type(settings_app.SCRIPT_TEMP_STDOUT_PATH) == unicode, type(settings_app.SCRIPT_TEMP_STDOUT_PATH)
            assert type(self.xml_original) == unicode, type(self.xml_original)
            ## save file w/identifier as part of name
            file_name_root = u'FILE_%s' % random.randint(1000,9999)    # need this root part later
            file_name = u'%s.xml' % file_name_root
            # updateLog( '- in common.runMungerNew(); file_name is: %s' % file_name, log_identifier )
            file_path = u'%s/%s' % ( settings_app.MUNGER_SCRIPT_XML_DIRECTORY, file_name )
            f = open( file_path, u'w' )
            f.write( self.xml_original.encode(u'utf-8') )
            f.close()
            ## call script (called script automatically saves file in various processing and a final directory)
            current_working_directory = os.getcwd()
            os.chdir( settings_app.MUNGER_SCRIPT_DIRECTORY )
            var = u'1'    # days; required by script; tells script to process all files updated in last day
            command_list = [ u'./strip.pl', var ]
            ## open temp files
            f_stdout = open( settings_app.SCRIPT_TEMP_STDOUT_PATH, u'w' )
            f_stderr = open( settings_app.SCRIPT_TEMP_STDERR_PATH, u'w' )
            f_stdout.write( u'' )
            f_stderr.write( u'' )
            ## run command
            subprocess.call( command_list, stdout=f_stdout, stderr=f_stderr )
            ## populate output
            f_stdout.close()
            f_stderr.close()
            ## read output file into string
            file_path = u'%s/%s' % ( settings_app.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY, file_name )
            f = open( file_path )
            munged_xml_string = f.read()
            assert type(munged_xml_string) == str, type(munged_xml_string)
            munged_xml_ustring = munged_xml_string.decode(u'utf-8')
            f.close()
            ## cleanup & return
            files_to_delete = [
                u'%s/%s' % ( settings_app.MUNGER_SCRIPT_XML_DIRECTORY, file_name ),
                u'%s/%s' % ( settings_app.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY, file_name ),
                u'%s/Cloned/%s.cloned.xml' % ( settings_app.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
                u'%s/Copied/%s' % ( settings_app.MUNGER_SCRIPT_DIRECTORY, file_name ),
                u'%s/Decomposed/%s.cloned.decomposed.xml' % ( settings_app.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
                u'%s/Final/%s' % ( settings_app.MUNGER_SCRIPT_DIRECTORY, file_name ),
                u'%s/Stripped/%s.cloned.decomposed.stripped.xml' % ( settings_app.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
                ]
            for entry in files_to_delete:
                assert os.path.exists(entry) == True, os.path.exists(entry)
                os.remove( entry )
                assert os.path.exists(entry) == False, os.path.exists(entry)
            os.chdir( current_working_directory )    # otherwise may affect other scripts
            self.xml_munged = munged_xml_ustring
            self.save()
        except Exception, e:
            message = common.makeErrorString()
            self.problem_log = smart_unicode( message )
            self.save()
        # end def runMunger()

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
