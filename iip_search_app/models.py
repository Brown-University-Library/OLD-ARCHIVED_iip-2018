# -*- coding: utf-8 -*-

import datetime, glob, json, logging, os, pprint, random, subprocess, time
import envoy, redis, requests, rq
from lxml import etree


log = logging.getLogger(__name__)


class ProcessorUtils( object ):
    """ Container for support-tasks for processing inscriptions -- actual processing tasks handled by Processor().
        Non-django, plain-python model.
        No dango dependencies, including settings. """

    def __init__( self ):
        """ Settings. """
        self.XML_DIR_PATH = unicode( os.environ.get(u'IIP_SEARCH__XML_DIR_PATH') )
        self.SOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__SOLR_URL') )
        self.DISPLAY_STATUSES_BACKUP_DIR = unicode( os.environ.get(u'IIP_SEARCH__DISPLAY_STATUSES_BACKUP_DIR') )
        self.DISPLAY_STATUSES_BACKUP_TIMEFRAME_IN_DAYS = int( os.environ.get(u'IIP_SEARCH__DISPLAY_STATUSES_BACKUP_TIMEFRAME_IN_DAYS') )

    def call_svn_update( self ):
        """ Runs svn update.
                Returns list of filenames.
            Called by (eventually) queue-task grab_updates(). """
        command = u'svn update %s' % self.XML_DIR_PATH
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        std_out = r.std_out.decode(u'utf-8')
        result_dict = self.parse_update_output( std_out )
        return {
            u'status_code': r.status_code,
            u'std_out': std_out,
            u'std_err': r.std_err.decode(u'utf-8'),
            u'command': r.command,
            u'history': r.history,
            u'file_ids': result_dict[u'file_ids'] }

    def parse_update_output( self, std_out ):
        """ Takes envoy stdout string.
                Tries to create file_ids list.
                Returns file list.
            Called by self.call_svn_update(). """
        assert type(std_out) == unicode
        file_ids = []
        lines = std_out.split()
        for line in lines:
            if u'.xml' in line:
                segments = line.split( u'/' )
                file_ids.append( segments[-1][:-4] )  # last segment is abc.xml; file_id is all but last 4 characters
        return { u'file_ids': sorted(file_ids) }

    def backup_display_statuses( self ):
        """ Queries solr for current display-statuses and saves them to a json file.
            Called by iip_search_app.models.run_delete_orphans() and eventually any other multi-index updater. """
        url = u'%s/select?q=*:*&rows=6000&fl=inscription_id,display_status&wt=json&indent=true' % self.SOLR_URL
        r = requests.get( url )
        filename = u'display_statuses_backup_%s.json' % unicode( datetime.datetime.now() ).replace( u' ', u'_' )
        filepath = u'%s/%s' % ( self.DISPLAY_STATUSES_BACKUP_DIR, filename )
        with open( filepath, u'w' ) as f:
            f.write( r.content )
        self.delete_old_backups()
        return

    def delete_old_backups( self ):
        """ Deletes old backup display status files.
            Called by self.backup_display_statuses() """
        now = time.time()
        seconds_in_day = 60*60*24
        timeframe_days = seconds_in_day * self.DISPLAY_STATUSES_BACKUP_TIMEFRAME_IN_DAYS
        for backup_filename in os.listdir( self.DISPLAY_STATUSES_BACKUP_DIR ):
            backup_filepath = u'%s/%s' % ( self.DISPLAY_STATUSES_BACKUP_DIR, backup_filename )
            if os.stat( backup_filepath ).st_mtime < now - timeframe_days:
                os.remove( backup_filepath )
        return

    def validate_inscription_id( self, inscription_id ):
        """ Ensures inscription_id is valid.
            Returns boolean.
            Called by (queue runner) iip_search_app.models.run_process_single_file(). """
        killer = OrphanKiller( log )
        solr_inscription_ids = killer.build_solr_inscription_ids()
        validity = inscription_id in solr_inscription_ids
        log.info( u'in iip_search_app.models.ProcessorUtils.validate_inscription_id(); validity, `%s`' % unicode(repr(validity)) )
        return validity

    def grab_current_display_status( self, inscription_id ):
        """ Grabs and returns the current display status for given inscription_id.
            Called by (queue runner) iip_search_app.models.run_process_single_file(). """
        url = u'%s/select?q=*:*&rows=6000&fl=inscription_id,display_status&wt=json&indent=true' % self.SOLR_URL
        r = requests.get( url )
        d = r.json()
        dicts = d[u'response'][u'docs']  # [ {u'display_status': u'to_approve', u'inscription_id': u'jeru0237'}, {etc} ]
        found_display_status = u'init'
        for dct in dicts:
            if dct[u'inscription_id'] == inscription_id:
                found_display_status = dct[u'display_status']
                break
        log.info( u'in iip_search_app.models.ProcessorUtils.grab_current_display_status(); found_display_status, `%s`' % found_display_status )
        return found_display_status

    ## end class ProcessorUtils()


class Processor( object ):
    """ Container for various tasks involved in processing metadata for a _single_ inscription.
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
        self.SOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__SOLR_URL') )

    def process_file( self, file_id, grab_latest_file, display_status ):
        """ Takes file_id string.
                Runs svn-export on file if grab_latest_file=True,
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
            u'a__grab_latest_file': None,
            u'b__grab_source_xml': None,
            u'c__run_munger': None,
            u'd__make_initial_solr_doc': None,
            u'e__update_display_facet': None,
            u'f__post_to_solr': None
            }
        process_dict[u'a__grab_latest_file'] = self.grab_latest_file(
            file_id )
        process_dict[u'b__grab_source_xml'] = self.grab_original_xml(
            file_id )
        process_dict[u'c__run_munger'] = self.run_munger(
            source_xml=process_dict[u'b__grab_source_xml'][u'xml'] )
        process_dict[u'd__make_initial_solr_doc'] = self.make_initial_solr_doc(
            munged_xml=process_dict[u'c__run_munger'][u'munged_xml'] )
        process_dict[u'e__update_display_facet'] = self.update_display_facet(
            initial_solr_xml=process_dict[u'd__make_initial_solr_doc'][u'transformed_xml'], display_status=display_status )
        process_dict[u'f__post_to_solr'] = self.update_solr(
            updated_solr_xml=process_dict[u'e__update_display_facet'][u'updated_xml'] )
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
        log.info( u'in models.Processor.grab_latest_file(); return_dict, ```%s```' % unicode(pprint.pformat(return_dict)) )
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
        log.info( u'in models.Processor.grab_original_xml(); return_dict, ```%s```' % unicode(pprint.pformat(return_dict)) )
        return return_dict

    ##

    def run_munger( self, source_xml ):
        """ TEMPORARILY BYPASSES MUNGER.
            Called by process_file(). """
        self._run_munger_asserts( source_xml )  # validates input-data type
        munged_xml = source_xml
        return_dict = {
            u'source_xml': source_xml,
            u'munged_xml': munged_xml
            }
        log.info( u'in models.Processor.run_munger(); return_dict, ```%s```' % unicode(pprint.pformat(return_dict)) )
        return return_dict

    # def run_munger( self, source_xml ):
    #     """ Takes source xml unicode string.
    #             Applies perl munger.
    #             Returns processed xml unicode string.
    #         Called by process_file(). """
    #     self._run_munger_asserts( source_xml )  # validates input-data type
    #     ( file_name, file_name_root ) = self._save_source_xml( source_xml )  # saves source-xml to to-be-munged directory
    #     ( f_stdout, f_stderr, temp_stdout_filepath, temp_stderr_filepath ) = self._setup_munger_stdstuff()
    #     current_working_directory = self._call_munger( f_stdout, f_stderr )
    #     self._close_munger_stdstuff( f_stdout, f_stderr, temp_stdout_filepath, temp_stderr_filepath )
    #     munged_xml = self._get_munged_xml( file_name )
    #     self._delete_munger_detritus( file_name, file_name_root, current_working_directory )
    #     return_dict = {
    #         u'source_xml': source_xml,
    #         u'munged_xml': munged_xml
    #         }
    #     log.info( u'in models.Processor.run_munger(); return_dict, ```%s```' % unicode(pprint.pformat(return_dict)) )
    #     return return_dict

    def _run_munger_asserts( self, source_xml ):
        """ Takes source_xml.
                Runs type asserts.
            Called by run_munger(). """
        assert type(source_xml) == unicode, type(source_xml)
        assert type(self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY) == unicode, type(self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY)
        assert type(self.MUNGER_SCRIPT_XML_DIRECTORY) == unicode, type(self.MUNGER_SCRIPT_XML_DIRECTORY)
        assert type(self.TEMPFILES_DIR_PATH) == unicode, type(self.TEMPFILES_DIR_PATH)
        log.info( u'in models.Processor._run_munger_asserts(); source_xml & paths all unicode' )
        return

    def _save_source_xml( self, source_xml ):
        """ Takes source_xml.
                Gives it a unique filename and saves it to directory for subsequent script call.
                Returns file_name and file_name_root strings.
            Called by run_munger(). """
        ## save file w/identifier as part of name
        file_name_root = u'FILE_%s' % random.randint(1000,9999)    # need this root part later
        file_name = u'%s.xml' % file_name_root
        filepath = u'%s/%s' % ( self.MUNGER_SCRIPT_XML_DIRECTORY, file_name )
        log.info( u'in iip_search_app.models.Processor._save_source_xml(); filepath, `%s`' % filepath )
        f = open( filepath, u'w' )
        f.write( source_xml.encode(u'utf-8') )
        f.close()
        return ( file_name, file_name_root )

    def _setup_munger_stdstuff( self ):
        """ Sets up and returns stderr and stdout file-objects and paths.
            Called by run_munger(). """
        ( temp_stdout_filepath, temp_stderr_filepath ) = ( self._make_temp_filepath(u'stdout_munger'), self._make_temp_filepath(u'stderr_munger') )
        log.info( u'in iip_search_app.models.Processor._setup_munger_stdstuff(); temp_stdout_filepath, `%s`' % temp_stdout_filepath )
        log.info( u'in iip_search_app.models.Processor._setup_munger_stdstuff(); temp_stderr_filepath, `%s`' % temp_stderr_filepath )
        f_stdout = open( temp_stdout_filepath, u'w' )
        f_stderr = open( temp_stderr_filepath, u'w' )
        f_stdout.write( u'' )
        f_stderr.write( u'' )
        return ( f_stdout, f_stderr, temp_stdout_filepath, temp_stderr_filepath )

    def _call_munger( self, f_stdout, f_stderr):
        """ Takes stdout and stderr file-objects.
                Sets cwd and calls perl script.
                Returns current_working_directory.
            Called by run_munger(). """
        time.sleep( .2 )
        ## setup call
        current_working_directory = os.getcwd()
        log.info( u'in iip_search_app.models.Processor._call_munger(); initial current_working_directory, `%s`' % current_working_directory )
        log.info( u'in iip_search_app.models.Processor._call_munger(); changing to directory, `%s`' % self.MUNGER_SCRIPT_DIRECTORY )
        os.chdir( self.MUNGER_SCRIPT_DIRECTORY )
        var = u'1'    # days; required by script; tells script to process all files updated in last day
        command_list = [ u'./strip.pl', var ]
        ## run command
        subprocess.call( command_list, stdout=f_stdout, stderr=f_stderr )  # called script saves temp-files in various directories
        time.sleep( .2 )
        return current_working_directory

    def _close_munger_stdstuff( self, f_stdout, f_stderr, temp_stdout_filepath, temp_stderr_filepath ):
        """ Takes stdout and stderr file objects and filepaths.
                Closes and deletes them.
            Called by run_munger(). """
        f_stdout.close()
        f_stderr.close()
        f_stdout = open( temp_stdout_filepath, u'r' )
        f_stderr = open( temp_stderr_filepath, u'r' )
        var_stdout = f_stdout.readlines()
        log.info( u'in iip_search_app.models.Processor._close_munger_stdstuff(); var_stdout just before deletion, `%s`' % var_stdout )
        var_stderr = f_stderr.readlines()
        log.info( u'in iip_search_app.models.Processor._close_munger_stdstuff(); var_stderr just before deletion, `%s`' % var_stderr )
        f_stdout.close()
        f_stderr.close()
        os.remove( temp_stdout_filepath )
        os.remove( temp_stderr_filepath )
        return

    def _get_munged_xml( self, file_name ):
        """ Takes file_name.
                Opens and reads the munged file.
                Returns the string.
            Called by run_munger(). """
        filepath = u'%s/%s' % ( self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY, file_name )
        log.info( u'in iip_search_app.models.Processor._get_munged_xml(); filepath, `%s`' % filepath )
        f = open( filepath )
        munged_utf8_xml = f.read()
        assert type(munged_utf8_xml) == str, type(munged_utf8_xml)
        munged_xml = munged_utf8_xml.decode(u'utf-8')
        f.close()
        return munged_xml

    def _delete_munger_detritus( self, file_name, file_name_root, current_working_directory ):
        """ Takes file_name and path info and current_working_directory.
                Deletes temp working files and resets original current_working_directory.
            Called by run_munger(). """
        files_to_delete = [
            u'%s/%s' % ( self.MUNGER_SCRIPT_XML_DIRECTORY, file_name ),
            u'%s/%s' % ( self.MUNGER_SCRIPT_MUNGED_XML_DIRECTORY, file_name ),
            u'%s/Cloned/%s.cloned.xml' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
            u'%s/Copied/%s' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name ),
            u'%s/Decomposed/%s.cloned.decomposed.xml' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
            u'%s/Final/%s' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name ),
            u'%s/Stripped/%s.cloned.decomposed.stripped.xml' % ( self.MUNGER_SCRIPT_DIRECTORY, file_name_root ),
            ]
        for entry in files_to_delete:
            log.info( u'in iip_search_app.models.Processor._delete_munger_detritus(); file in process, `%s`' % entry )
            if os.path.exists( entry ):
                log.info( u'in iip_search_app.models.Processor._delete_munger_detritus(); file exists' )
                os.remove( entry )
                log.info( u'in iip_search_app.models.Processor._delete_munger_detritus(); file removed' )
                assert os.path.exists(entry) == False, os.path.exists(entry)
                log.info( u'in iip_search_app.models.Processor._delete_munger_detritus(); removal confirmed' )
            else:
               log.info( u'in iip_search_app.models.Processor._delete_munger_detritus(); file does not exist' )
        os.chdir( current_working_directory )    # otherwise may affect other scripts
        return

    ##

    def make_initial_solr_doc( self, munged_xml ):
        """ Takes munged xml unicode string.
                Applies xsl transformation to create a solr doc.
                Returns processed xml in dict.
            Called by process_file(). """
        assert type(self.SOLR_DOC_STYLESHEET_PATH) == unicode, type(self.SOLR_DOC_STYLESHEET_PATH)
        assert type(self.TRANSFORMER_URL) == unicode, type(self.TRANSFORMER_URL)
        assert type(munged_xml) == unicode, type(munged_xml)
        log.info( u'in models.Processor.make_initial_solr_doc(); self.SOLR_DOC_STYLESHEET_PATH, ```%s```' % self.SOLR_DOC_STYLESHEET_PATH )
        log.info( u'in models.Processor.make_initial_solr_doc(); self.TRANSFORMER_URL, ```%s```' % self.TRANSFORMER_URL )
        iip_solrdoc_string = 'init'
        ## get stylesheet
        f = open( self.SOLR_DOC_STYLESHEET_PATH )
        stylesheet_string = f.read()
        f.close()
        assert type(stylesheet_string) == str, type(stylesheet_string)
        stylesheet_ustring = stylesheet_string.decode(u'utf-8')
        ## hit the post xslt transformer
        url = self.TRANSFORMER_URL
        payload = {
            u'source_string': munged_xml,
            u'stylesheet_string': stylesheet_ustring }
        headers = { u'content-type': u'text/xml; charset=utf-8' }
        r = requests.post( url, data=payload, headers=headers )
        transformed_xml = r.content.decode(u'utf-8')
        return_dict = {
            u'initial_munged_xml': munged_xml,
            u'stylesheet_xml': stylesheet_ustring,
            u'transformed_xml': transformed_xml
            }
        log.info( u'in models.Processor.make_initial_solr_doc(); return_dict, ```%s```' % unicode(pprint.pformat(return_dict)) )
        return return_dict

    ##

    def update_display_facet( self, initial_solr_xml, display_status ):
        """ Takes transformed initial solr xml.
                Doc-i-fies it and adds a display_status node.
                Returns updated xml in dict.
            Called by process_file().
            Note: normally, vcs updates should trigger the display_status: u'to_approve'. """
        assert type(initial_solr_xml) == unicode, type(initial_solr_xml)
        assert display_status in [ u'to_approve', u'to_correct', u'approved' ]
        doc = etree.fromstring( initial_solr_xml.encode(u'utf-8'))    # can't take unicode string due to xml file's encoding declaration
        node = doc.xpath( u'//doc' )[0]
        new_field = etree.SubElement( node, u'field' )
        new_field.attrib[u'name'] = u'display_status'
        new_field.text = display_status
        utf8_xml = etree.tostring( doc, encoding=u'UTF-8', xml_declaration=True, pretty_print=False )
        assert type(utf8_xml) == str, type(utf8_xml)
        updated_xml = utf8_xml.decode(u'utf-8')
        return { u'initial_solr_xml': initial_solr_xml, u'updated_xml': updated_xml }

    ##

    def update_solr( self, updated_solr_xml ):
        """ Takes solr xml unicode string.
                Posts it to solr.
                Returns response dict.
            Called by process_file(). """
        assert type(self.SOLR_URL) == unicode, type(self.SOLR_URL)
        assert type(updated_solr_xml) == unicode, type(updated_solr_xml)
        update_url = u'%s/update/?commit=true' % self.SOLR_URL
        headers = { 'content-type': 'text/xml; charset=utf-8' }    # from testing, NON-unicode-string posts were bullet-proof
        r = requests.post(
            update_url.encode(u'utf-8'),
            headers=headers,
            data=updated_solr_xml.encode(u'utf-8') )
        return_dict = {
            u'response_status_code': r.status_code, u'response_text': r.content.decode(u'utf-8'), u'submitted_xml': updated_solr_xml }
        return return_dict

    ## end class Processor()


class OrphanKiller( object ):
    """ Container for various tasks involved in deleting orphaned inscription data from the solr index.
        Non-django, plain-python model.
        No dango dependencies, including settings. """

    def __init__( self, log ):
        """ Settings. """
        self.XML_DIR_PATH = unicode( os.environ.get(u'IIP_SEARCH__XML_DIR_PATH') )
        self.SOLR_URL = unicode( os.environ.get(u'IIP_SEARCH__SOLR_URL') )
        self.log = log

    def build_directory_inscription_ids( self ):
        """ Returns list of file-system ids.
            Called by (queue-runner) models.run_delete_orphans(). """
        self.log.info( u'in models.OrphanKiller.build_directory_inscription_ids(); inscriptions_dir_path, `%s`' % self.XML_DIR_PATH )
        inscription_paths = glob.glob( u'%s/*.xml' % self.XML_DIR_PATH )
        self.log.info( u'in models.OrphanKiller.build_directory_inscription_ids(); len(inscription_paths), `%s`; inscription_paths[0:3], `%s`' % (len(inscription_paths), pprint.pformat(inscription_paths[0:3]) ) )
        directory_inscription_ids = []
        for path in inscription_paths:
            filename = path.split( u'/' )[-1]
            inscription_id = filename.split( u'.xml' )[0]
            directory_inscription_ids.append( inscription_id )
        directory_inscription_ids = sorted( directory_inscription_ids )
        self.log.info( u'in models.OrphanKiller.build_directory_inscription_ids(); len(directory_inscription_ids), `%s`; directory_inscription_ids[0:3], `%s`' % (len(directory_inscription_ids), pprint.pformat(directory_inscription_ids[0:3])) )
        return directory_inscription_ids

    def build_solr_inscription_ids( self ):
        """ Returns list of solr inscription ids.
            Called by (queue-runner) models.run_delete_orphans(). """
        url = u'%s/select?q=*:*&fl=inscription_id&rows=100000&wt=json' % self.SOLR_URL
        self.log.info( u'in models.OrphanKiller.build_solr_inscription_ids(); url, `%s`' % url )
        r = requests.get( url )
        json_dict = r.json()
        docs = json_dict[u'response'][u'docs']  # list of dicts
        solr_inscription_ids = []
        for doc in docs:
            solr_inscription_ids.append( doc[u'inscription_id'] )
        solr_inscription_idssolr_inscription_ids = sorted( solr_inscription_ids )
        self.log.info( u'in models.OrphanKiller.build_solr_inscription_ids(); len(solr_inscription_ids), `%s`; solr_inscription_ids[0:3], `%s`' % (len(solr_inscription_ids), pprint.pformat(solr_inscription_ids[0:3])) )
        return solr_inscription_ids

    def build_orphan_list( self, directory_inscription_ids, solr_inscription_ids ):
        """ Returns list of solr-entries to delete.
            Called by (queue-runner) models.run_delete_orphans(). """
        directory_set = set( directory_inscription_ids )
        solr_set = set( solr_inscription_ids )
        deletion_set = solr_set - directory_set
        orphan_list = list( deletion_set )
        self.log.info( u'in models.OrphanKiller.build_orphan_list(); orphan_list, `%s`' % pprint.pformat(orphan_list) )
        return orphan_list

    def delete_orphan( self, inscription_id ):
        """ Deletes specified inscription_id from solr.
            Called by (queue-runner) models.run_delete_solr_entry(). """
        self.log.info( u'in models.OrphanKiller.delete_orphan(); inscription_id, `%s`' % inscription_id )
        s = solr.Solr( self.SOLR_URL )
        response = s.delete( inscription_id=inscription_id )
        s.commit()
        s.close()
        self.log.debug( u'in models.OrphanKiller.delete_orphan(); deletion-post complete; response is: %s' % response )
        return

    ## end class OrphanKiller()


class OneOff( object ):
    """ Container for one-off tasks that might again be useful in the future.
        Non-django, plain-python model.
        No dango dependencies, including settings. """

    def __init__( self ):
        self.log = logging.getLogger(__name__)


    def transfer_display_status( self ):
        """ Transfers display status from dev solr instance to production solr instance.
            Run directly. """
        ( old_solr_root_url, new_solr_root_url ) = ( unicode(os.environ.get(u'IIP_SEARCH__DEV_SOLR_URL')), unicode(os.environ.get(u'IIP_SEARCH__PRODUCTION_SOLR_URL'))  )
        old_solr_dct = self.grab_old_dict( old_solr_root_url )
        self.log.debug( u'source-data: `%s`' % pprint.pformat(old_solr_dct) )
        for i, ( inscription_id, display_status ) in enumerate( sorted(old_solr_dct.items()) ):
            print u'inscription_id, `%s`' % inscription_id
            if self.check_initial_status( new_solr_root_url, inscription_id, display_status ) == u'different':
                print u'updating!'
                self.update_new_solr( new_solr_root_url, inscription_id, display_status )
            if i > 6:
                break
        return

    def grab_old_dict( self, old_solr_root_url ):
        """ Grabs all ids & display-statuses and converts them to a dict.
            Called by transfer_display_status() """
        url = u'%s/select?q=*:*&rows=6000&fl=inscription_id,display_status&wt=json&indent=true' % old_solr_root_url
        r = requests.get( url )
        dct = r.json()
        lst = dct[u'response'][u'docs']
        assert sorted( lst[0].keys() ) == [u'display_status', u'inscription_id']
        new_dct = {}
        for dct in lst:
            new_dct[ dct[u'inscription_id'] ] = dct[u'display_status']
        return new_dct

    def check_initial_status( self, new_solr_root_url, inscription_id, target_display_status ):
        """ Checks production status before update.
            Called by transfer_display_status() """
        url = u'%s/select?q=inscription_id:%s&fl=inscription_id,display_status&wt=json&indent=true' % ( new_solr_root_url, inscription_id )
        r = requests.get( url )
        dct = r.json()
        data = dct[u'response'][u'docs'][0]
        self.log.debug( u'in OneOff.log_before_status(); initial data, `%s`' % data )
        if data[u'display_status'] == target_display_status:
            return_val = u'same'
        else:
            return_val = u'different'
        return return_val

    def update_new_solr( self, new_solr_root_url, inscription_id, display_status ):
        """ Peforms the update if necessary.
            Called by transfer_display_status() """
        url = u'%s/update?commit=true' % new_solr_root_url
        payload = [ { u'inscription_id': inscription_id, u'display_status': {u'set': display_status} } ]
        headers = { u'content-type': u'application/json; charset=utf-8' }
        r = requests.post( url, data=json.dumps(payload), headers=headers )
        self.log.debug( u'in OneOff.update_new_solr(); inscription_id, %s; solr-post-status-code, %s; updated_status, %s' % (inscription_id, r.status_code, display_status) )
        return




## queue runners ##

q = rq.Queue( u'iip', connection=redis.Redis() )

## triggered via views.py

def run_call_svn_update():
    """ Initiates svn update.
            Spawns a call to Processor.process_file() for each result found.
        Called by views.process(u'new') """
    log.info( u'in (queue-called) iip_search_app.models.run_call_svn_update(); starting at `%s`' % unicode(datetime.datetime.now()) )
    utils = ProcessorUtils()
    result_dict = utils.call_svn_update()
    log.info( u'in (queue-called) run_call_svn_update(); result_dict is, ```%s```' % pprint.pformat(result_dict) )
    for file_id in result_dict[u'file_ids']:
        job = q.enqueue_call (
            func=u'iip_search_app.models.run_process_file',
            kwargs = { u'file_id': file_id, u'grab_latest_file': True, u'display_status': u'to_approve' }
            )
    return

def run_delete_orphans():
    """ Initiates deletion of orphaned solr entries.
        Called by views.process( u'delete_orphans' ) """
    ( killer, utils ) = ( OrphanKiller(log), ProcessorUtils() )
    utils.backup_display_statuses()
    utils.call_svn_update()  # output not important; just need to ensure the xml-dir is fresh
    directory_inscription_ids = killer.build_directory_inscription_ids()
    solr_inscription_ids = killer.build_solr_inscription_ids()
    orphan_list = killer.build_orphan_list( directory_inscription_ids, solr_inscription_ids )
    for inscription_id in orphan_list:
        job = q.enqueue_call (
            func=u'iip_search_app.models.run_delete_solr_entry',
            kwargs = { u'inscription_id': inscription_id } )
    return

def run_process_single_file( inscription_id ):
    """ Triggers processing of single inscription.
        Called by views.process( u'INSCRIPTION_ID') """
    log.info( u'in iip_search_app.models.run_process_single_file(); starting at `%s`; inscription_id, `%s`' % (unicode(datetime.datetime.now()), inscription_id) )
    utils = ProcessorUtils()
    if utils.validate_inscription_id( inscription_id ) == False:
        return
    utils.backup_display_statuses()
    current_display_status = utils.grab_current_display_status( inscription_id )
    q.enqueue_call(
        func = u'iip_search_app.models.run_process_file',
        kwargs = { u'file_id': inscription_id, u'grab_latest_file': True, u'display_status': current_display_status }
        )
    return

def run_process_all_files():
    """ Triggers processing of all inscriptions.
        Note: initially had this function grab display_status then call `run_process_file` directly,
              but x-thousand display-status url-calls from single job timed out.
        Called by views.process( u'all') """
    log.info( u'in iip_search_app.models.run_process_all_files(); starting at `%s`' % unicode(datetime.datetime.now()) )
    ( killer, utils ) = ( OrphanKiller(log), ProcessorUtils() )
    utils.backup_display_statuses()
    utils.call_svn_update()  # run svn update to get most recent info
    directory_inscription_ids = killer.build_directory_inscription_ids()  # get list of directory-inscription-ids
    for inscription_id in directory_inscription_ids:
        q.enqueue_call(
            func = u'iip_search_app.models.run_grab_status_then_process_file',
            kwargs = { u'inscription_id': inscription_id } )
    return

## triggered by one of above queue-runners

def run_process_file( file_id, grab_latest_file, display_status ):
    """ Calls Processor.process_file().
        Called by (queue-runner) iip_search_app.models.run_call_svn_update().
                  (queue-runner) iip_search_app.models.run_process_single_file().
                  (queue-runner) iip_search_app.models.run_grab_status_then_process_file(). """
    log.info( u'in (queue-runner) iip_search_app.models.run_process_file(); starting at `%s`; file_id, `%s`' % (unicode(datetime.datetime.now()), file_id) )
    if file_id in [ u'include_publicationStmt', u'include_taxonomies', u'interpretations', u'names', u'persons' ]:
        log.info( u'in (queue-runner) iip_search_app.models.run_process_file(); file_id in ignore list; skipping' )
        return
    processor = Processor()
    process_dict = processor.process_file( file_id, grab_latest_file, display_status )
    log.info( u'in (queue-runner) iip_search_app.models.run_process_file(); process_dict is, ```%s```' % pprint.pformat(process_dict) )
    return

def run_delete_solr_entry( inscription_id ):
    """ Calls OrphanKiller.delete_solr_entry().
        Called by (queue-runner) iip_search_app.models.run_delete_orphans(). """
    killer = OrphanKiller( log )
    log.info( u'in (queue-runner) iip_search_app.models.run_delete_solr_entry(); deleting solr inscription_id, `%s`' % inscription_id )
    killer.delete_orphan( inscription_id )
    return

def run_grab_status_then_process_file( inscription_id ):
    """ Grabs current display_status and processes file.
        Called by (queue-runner) iip_search_app.models.run_process_all_files() """
    utils = ProcessorUtils()
    current_display_status = utils.grab_current_display_status( inscription_id )
    log.info( u'in (queue-runner) iip_search_app.models.run_grab_status_then_process_file(); starting at `%s`' % unicode(datetime.datetime.now()) )
    q.enqueue_call(
        func = u'iip_search_app.models.run_process_file',
        kwargs = { u'file_id': inscription_id, u'grab_latest_file': True, u'display_status': current_display_status }
        )
    return

## eof
