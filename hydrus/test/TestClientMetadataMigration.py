import json
import os
import unittest

from hydrus.core import HydrusConstants as HC
from hydrus.core import HydrusData
from hydrus.core import HydrusText
from hydrus.core import HydrusTime

from hydrus.client import ClientConstants as CC
from hydrus.client import ClientStrings
from hydrus.client import ClientTime
from hydrus.client.media import ClientMediaManagers
from hydrus.client.media import ClientMediaResult
from hydrus.client.metadata import ClientContentUpdates
from hydrus.client.metadata import ClientMetadataMigration
from hydrus.client.metadata import ClientMetadataMigrationExporters
from hydrus.client.metadata import ClientMetadataMigrationImporters
from hydrus.client.metadata import ClientTags
from hydrus.client.parsing import ClientParsing

from hydrus.test import HelperFunctions as HF
from hydrus.test import TestGlobals as TG

class TestSingleFileMetadataRouter( unittest.TestCase ):
    
    def test_router( self ):
        
        my_current_storage_tags = { 'samus aran', 'blonde hair' }
        my_current_display_tags = { 'character:samus aran', 'blonde hair' }
        repo_current_storage_tags = { 'lara croft' }
        repo_current_display_tags = { 'character:lara croft' }
        repo_pending_storage_tags = { 'tomb raider' }
        repo_pending_display_tags = { 'series:tomb raider' }
        
        service_keys_to_statuses_to_storage_tags = {
            CC.DEFAULT_LOCAL_TAG_SERVICE_KEY : {
                HC.CONTENT_STATUS_CURRENT : my_current_storage_tags
            },
            TG.test_controller.example_tag_repo_service_key : {
                HC.CONTENT_STATUS_CURRENT : repo_current_storage_tags,
                HC.CONTENT_STATUS_PENDING : repo_pending_storage_tags
            }
        }
        
        service_keys_to_statuses_to_display_tags = {
            CC.DEFAULT_LOCAL_TAG_SERVICE_KEY : {
                HC.CONTENT_STATUS_CURRENT : my_current_display_tags
            },
            TG.test_controller.example_tag_repo_service_key : {
                HC.CONTENT_STATUS_CURRENT : repo_current_display_tags,
                HC.CONTENT_STATUS_PENDING : repo_pending_display_tags
            }
        }
        
        # duplicate to generate proper dicts
        
        tags_manager = ClientMediaManagers.TagsManager(
            service_keys_to_statuses_to_storage_tags,
            service_keys_to_statuses_to_display_tags
        ).Duplicate()
        
        #
        
        hash = HydrusData.GenerateKey()
        size = 40960
        mime = HC.IMAGE_JPEG
        width = 640
        height = 480
        duration_ms = None
        num_frames = None
        has_audio = False
        num_words = None
        
        times_manager = ClientMediaManagers.TimesManager()
        
        times_manager.SetImportedTimestampMS( CC.LOCAL_FILE_SERVICE_KEY, 123000 )
        times_manager.SetImportedTimestampMS( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, 123000 )
        
        inbox = True
        
        local_locations_manager = ClientMediaManagers.LocationsManager( { CC.LOCAL_FILE_SERVICE_KEY, CC.COMBINED_LOCAL_FILE_SERVICE_KEY }, set(), set(), set(), times_manager, inbox )
        
        ratings_manager = ClientMediaManagers.RatingsManager( {} )
        
        notes_manager = ClientMediaManagers.NotesManager( {} )
        
        file_viewing_stats_manager = ClientMediaManagers.FileViewingStatsManager.STATICGenerateEmptyManager( times_manager )
        
        #
        
        file_info_manager = ClientMediaManagers.FileInfoManager( 1, hash, size, mime, width, height, duration_ms, num_frames, has_audio, num_words )
        
        media_result = ClientMediaResult.MediaResult( file_info_manager, tags_manager, times_manager, local_locations_manager, ratings_manager, notes_manager, file_viewing_stats_manager )
        
        #
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        
        expected_output_path = actual_file_path + '.txt'
        
        # empty, works ok but does nothing
        
        router = ClientMetadataMigration.SingleFileMetadataRouter( importers = [], string_processor = None, exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT() )
        
        router.Work( media_result, actual_file_path )
        
        self.assertFalse( os.path.exists( expected_output_path ) )
        
        # doing everything
        
        rows_1 = [ 'character:samus aran', 'blonde hair' ]
        rows_2 = [ 'character:lara croft', 'brown hair' ]
        
        expected_input_path_1 = actual_file_path + '.1.txt'
        
        with open( expected_input_path_1, 'w', encoding = 'utf-8' ) as f:
            
            f.write( '\n'.join( rows_1 ) )
            
        
        importer_1 = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT( suffix = '1' )
        
        expected_input_path_2 = actual_file_path + '.2.txt'
        
        with open( expected_input_path_2, 'w', encoding = 'utf-8' ) as f:
            
            f.write( '\n'.join( rows_2 ) )
            
        
        importer_2 = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT( suffix = '2' )
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        router = ClientMetadataMigration.SingleFileMetadataRouter( importers = [ importer_1, importer_2 ], string_processor = string_processor, exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT() )
        
        router.Work( media_result, actual_file_path )
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        os.unlink( expected_input_path_1 )
        os.unlink( expected_input_path_2 )
        
        result = HydrusText.DeserialiseNewlinedTexts( text )
        expected_result = string_processor.ProcessStrings( set( rows_1 ).union( rows_2 ) )
        
        self.assertTrue( len( result ) > 0 )
        self.assertEqual( set( result ), set( expected_result ) )
        
    

class TestSingleFileMetadataImporters( unittest.TestCase ):
    
    def test_media_tags( self ):
        
        my_current_storage_tags = { 'samus aran', 'blonde hair' }
        my_current_display_tags = { 'character:samus aran', 'blonde hair' }
        repo_current_storage_tags = { 'lara croft' }
        repo_current_display_tags = { 'character:lara croft' }
        repo_pending_storage_tags = { 'tomb raider' }
        repo_pending_display_tags = { 'series:tomb raider' }
        
        service_keys_to_statuses_to_storage_tags = {
            CC.DEFAULT_LOCAL_TAG_SERVICE_KEY : {
                HC.CONTENT_STATUS_CURRENT : my_current_storage_tags
            },
            TG.test_controller.example_tag_repo_service_key : {
                HC.CONTENT_STATUS_CURRENT : repo_current_storage_tags,
                HC.CONTENT_STATUS_PENDING : repo_pending_storage_tags
            }
        }
        
        service_keys_to_statuses_to_display_tags = {
            CC.DEFAULT_LOCAL_TAG_SERVICE_KEY : {
                HC.CONTENT_STATUS_CURRENT : my_current_display_tags
            },
            TG.test_controller.example_tag_repo_service_key : {
                HC.CONTENT_STATUS_CURRENT : repo_current_display_tags,
                HC.CONTENT_STATUS_PENDING : repo_pending_display_tags
            }
        }
        
        # duplicate to generate proper dicts
        
        tags_manager = ClientMediaManagers.TagsManager(
            service_keys_to_statuses_to_storage_tags,
            service_keys_to_statuses_to_display_tags
        ).Duplicate()
        
        #
        
        hash = HydrusData.GenerateKey()
        size = 40960
        mime = HC.IMAGE_JPEG
        width = 640
        height = 480
        duration_ms = None
        num_frames = None
        has_audio = False
        num_words = None
        
        times_manager = ClientMediaManagers.TimesManager()
        
        times_manager.SetImportedTimestampMS( CC.LOCAL_FILE_SERVICE_KEY, 123000 )
        times_manager.SetImportedTimestampMS( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, 123000 )
        
        inbox = True
        
        local_locations_manager = ClientMediaManagers.LocationsManager( { CC.LOCAL_FILE_SERVICE_KEY, CC.COMBINED_LOCAL_FILE_SERVICE_KEY }, set(), set(), set(), times_manager, inbox )
        
        ratings_manager = ClientMediaManagers.RatingsManager( {} )
        
        notes_manager = ClientMediaManagers.NotesManager( {} )
        
        file_viewing_stats_manager = ClientMediaManagers.FileViewingStatsManager.STATICGenerateEmptyManager( times_manager )
        
        #
        
        file_info_manager = ClientMediaManagers.FileInfoManager( 1, hash, size, mime, width, height, duration_ms, num_frames, has_audio, num_words )
        
        media_result = ClientMediaResult.MediaResult( file_info_manager, tags_manager, times_manager, local_locations_manager, ratings_manager, notes_manager, file_viewing_stats_manager )
        
        # simple local
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTags( service_key = CC.DEFAULT_LOCAL_TAG_SERVICE_KEY, tag_display_type = ClientTags.TAG_DISPLAY_STORAGE )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), set( my_current_storage_tags ) )
        
        #
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTags( service_key = CC.DEFAULT_LOCAL_TAG_SERVICE_KEY, tag_display_type = ClientTags.TAG_DISPLAY_DISPLAY_ACTUAL )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), set( my_current_display_tags ) )
        
        # simple repo
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTags( service_key = TG.test_controller.example_tag_repo_service_key )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), set( repo_current_display_tags ) )
        
        # all known
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTags( service_key = CC.COMBINED_TAG_SERVICE_KEY )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), set( my_current_display_tags ).union( repo_current_display_tags ) )
        
        # with string processor
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTags( string_processor = string_processor, service_key = CC.DEFAULT_LOCAL_TAG_SERVICE_KEY, tag_display_type = ClientTags.TAG_DISPLAY_DISPLAY_ACTUAL )
        
        result = importer.Import( media_result )
        
        self.assertTrue( len( result ) > 0 )
        self.assertNotEqual( set( result ), set( my_current_display_tags ) )
        self.assertEqual( set( result ), set( string_processor.ProcessStrings( my_current_display_tags ) ) )
        
    
    def test_media_notes( self ):
        
        names_to_notes = {
            'test' : 'This is a test note!',
            'Another Test' : 'This one has\n\na newline!'
        }
        
        expected_rows = [ '{}: {}'.format( name, note ) for ( name, note ) in names_to_notes.items() ]
        
        # simple
        
        hash = HydrusData.GenerateKey()
        
        media_result = HF.GetFakeMediaResult( hash )
        
        media_result.GetNotesManager().SetNamesToNotes( names_to_notes )
        
        # simple
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaNotes()
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), set( expected_rows ) )
        
        # with string processor
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaNotes( string_processor = string_processor )
        
        result = importer.Import( media_result )
        
        self.assertTrue( len( result ) > 0 )
        self.assertNotEqual( set( result ), set( expected_rows ) )
        self.assertEqual( set( result ), set( string_processor.ProcessStrings( expected_rows ) ) )
        
    
    def test_media_urls( self ):
        
        urls = { 'https://site.com/123456', 'https://cdn5.st.com/file/123456' }
        
        # simple
        
        hash = HydrusData.GenerateKey()
        size = 40960
        mime = HC.IMAGE_JPEG
        width = 640
        height = 480
        duration_ms = None
        num_frames = None
        has_audio = False
        num_words = None
        
        times_manager = ClientMediaManagers.TimesManager()
        
        times_manager.SetImportedTimestampMS( CC.LOCAL_FILE_SERVICE_KEY, 123000 )
        times_manager.SetImportedTimestampMS( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, 123000 )
        
        inbox = True
        
        local_locations_manager = ClientMediaManagers.LocationsManager( { CC.LOCAL_FILE_SERVICE_KEY, CC.COMBINED_LOCAL_FILE_SERVICE_KEY }, set(), set(), set(), times_manager, inbox, urls )
        
        # duplicate to generate proper dicts
        
        tags_manager = ClientMediaManagers.TagsManager( {}, {} ).Duplicate()
        
        ratings_manager = ClientMediaManagers.RatingsManager( {} )
        
        notes_manager = ClientMediaManagers.NotesManager( {} )
        
        file_viewing_stats_manager = ClientMediaManagers.FileViewingStatsManager.STATICGenerateEmptyManager( times_manager )
        
        #
        
        file_info_manager = ClientMediaManagers.FileInfoManager( 1, hash, size, mime, width, height, duration_ms, num_frames, has_audio, num_words )
        
        media_result = ClientMediaResult.MediaResult( file_info_manager, tags_manager, times_manager, local_locations_manager, ratings_manager, notes_manager, file_viewing_stats_manager )
        
        # simple
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaURLs()
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), set( urls ) )
        
        # with string processor
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaURLs( string_processor = string_processor )
        
        result = importer.Import( media_result )
        
        self.assertTrue( len( result ) > 0 )
        self.assertNotEqual( set( result ), set( urls ) )
        self.assertEqual( set( result ), set( string_processor.ProcessStrings( urls ) ) )
        
    
    def test_media_timestamps( self ):
        
        archived_timestamp_ms = HydrusTime.GetNowMS() - 3600000
        file_modified_timestamp_ms = HydrusTime.GetNowMS() - 2400000
        site_dot_com_modified_timestamp_ms = HydrusTime.GetNowMS() - 2500000
        timestamp_data_stub = ClientTime.TimestampData.STATICSimpleStub( HC.TIMESTAMP_TYPE_ARCHIVED )
        
        # simple
        
        hash = HydrusData.GenerateKey()
        size = 40960
        mime = HC.IMAGE_JPEG
        width = 640
        height = 480
        duration_ms = None
        num_frames = None
        has_audio = False
        num_words = None
        
        times_manager = ClientMediaManagers.TimesManager()
        
        times_manager.SetImportedTimestampMS( CC.LOCAL_FILE_SERVICE_KEY, 123000 )
        times_manager.SetImportedTimestampMS( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, 123000 )
        times_manager.SetArchivedTimestampMS( archived_timestamp_ms )
        times_manager.SetFileModifiedTimestampMS( file_modified_timestamp_ms )
        times_manager.SetDomainModifiedTimestampMS( 'site.com', site_dot_com_modified_timestamp_ms )
        
        inbox = True
        
        local_locations_manager = ClientMediaManagers.LocationsManager( { CC.LOCAL_FILE_SERVICE_KEY, CC.COMBINED_LOCAL_FILE_SERVICE_KEY }, set(), set(), set(), times_manager, inbox, set() )
        
        # duplicate to generate proper dicts
        
        tags_manager = ClientMediaManagers.TagsManager( {}, {} ).Duplicate()
        
        ratings_manager = ClientMediaManagers.RatingsManager( {} )
        
        notes_manager = ClientMediaManagers.NotesManager( {} )
        
        file_viewing_stats_manager = ClientMediaManagers.FileViewingStatsManager.STATICGenerateEmptyManager( times_manager )
        
        #
        
        file_info_manager = ClientMediaManagers.FileInfoManager( 1, hash, size, mime, width, height, duration_ms, num_frames, has_audio, num_words )
        
        media_result = ClientMediaResult.MediaResult( file_info_manager, tags_manager, times_manager, local_locations_manager, ratings_manager, notes_manager, file_viewing_stats_manager )
        
        # simple
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTimestamps()
        importer.SetTimestampDataStub( timestamp_data_stub )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), { str( HydrusTime.SecondiseMS( archived_timestamp_ms ) ) } )
        
        # with string processor
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_DATE_ENCODE, ( '%Y-%m-%d %H:%M:%S', 0 ) ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTimestamps( string_processor = string_processor )
        importer.SetTimestampDataStub( timestamp_data_stub )
        
        result = importer.Import( media_result )
        
        self.assertTrue( len( result ) > 0 )
        self.assertNotEqual( set( result ), { str( HydrusTime.SecondiseMS( archived_timestamp_ms ) ) } )
        self.assertEqual( set( result ), set( string_processor.ProcessStrings( { str( HydrusTime.SecondiseMS( archived_timestamp_ms ) ) } ) ) )
        
        # test modified date/aggregate
        
        timestamp_data_stub = ClientTime.TimestampData.STATICSimpleStub( HC.TIMESTAMP_TYPE_MODIFIED_FILE )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTimestamps()
        importer.SetTimestampDataStub( timestamp_data_stub )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), { str( HydrusTime.SecondiseMS( file_modified_timestamp_ms ) ) } )
        
        #
        
        timestamp_data_stub = ClientTime.TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_MODIFIED_DOMAIN, location = 'site.com' )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTimestamps()
        importer.SetTimestampDataStub( timestamp_data_stub )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), { str( HydrusTime.SecondiseMS( site_dot_com_modified_timestamp_ms ) ) } )
        
        #
        
        timestamp_data_stub = ClientTime.TimestampData.STATICSimpleStub( HC.TIMESTAMP_TYPE_MODIFIED_AGGREGATE )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterMediaTimestamps()
        importer.SetTimestampDataStub( timestamp_data_stub )
        
        result = importer.Import( media_result )
        
        self.assertEqual( set( result ), { str( HydrusTime.SecondiseMS( min( site_dot_com_modified_timestamp_ms, file_modified_timestamp_ms ) ) ) } )
        
    
    def test_media_txt( self ):
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        rows = [ 'character:samus aran', 'blonde hair' ]
        
        # simple
        
        expected_input_path = actual_file_path + '.txt'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( '\n'.join( rows ) )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT()
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertEqual( set( result ), set( rows ) )
        
        # carriage return
        
        expected_input_path = actual_file_path + '.txt'
        
        # we do a magic encode here, but actually in the read step python collapses the \r\n to a single \n anyway, but this is a good way to ensure all that anyway!
        with open( expected_input_path, 'wb' ) as f:
            
            f.write( '\r\n'.join( rows ).encode( 'utf-8' ) )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT()
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertEqual( set( result ), set( rows ) )
        
        # diff separator
        
        separator = ', '
        
        expected_input_path = actual_file_path + '.txt'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( separator.join( rows ) )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT( separator = separator )
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertEqual( set( result ), set( rows ) )
        
        # with suffix and processing
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        expected_input_path = actual_file_path + '.tags.txt'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( '\n'.join( rows ) )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT( string_processor = string_processor, suffix = 'tags' )
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertTrue( len( result ) > 0 )
        self.assertNotEqual( set( result ), set( rows ) )
        self.assertEqual( set( result ), set( string_processor.ProcessStrings( rows ) ) )
        
        # with filename remove ext and string conversion
        
        expected_input_path = os.path.join( TG.test_controller.db_dir, 'file.jpg'[1:].rsplit( '.', 1 )[0] ) + '.txt'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( '\n'.join( rows ) )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT( remove_actual_filename_ext = True, filename_string_converter = ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) )
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertTrue( len( result ) > 0 )
        self.assertEqual( set( result ), set( rows ) )
        
    
    def test_media_txt_multiline_note( self ):
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        rows = [ 'this is a multiline\n\nnote\nthe newline\ns\nmust stay intact!', 'here is\nanother one' ]
        
        # simple
        
        separator = '||||'
        
        expected_input_path = actual_file_path + '.txt'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( separator.join( rows ) )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterTXT( separator = separator )
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertEqual( set( result ), set( rows ) )
        
    
    def test_media_json( self ):
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        rows = [ 'character:samus aran', 'blonde hair' ]
        
        # no file means no rows
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterJSON()
        
        result = importer.Import( actual_file_path )
        
        self.assertEqual( set( result ), set() )
        
        # simple
        
        expected_input_path = actual_file_path + '.json'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            j = json.dumps( rows )
            
            f.write( j )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterJSON()
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertEqual( set( result ), set( rows ) )
        
        # with suffix, processing, and dest
        
        string_processor = ClientStrings.StringProcessor()
        
        processing_steps = [ ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) ]
        
        string_processor.SetProcessingSteps( processing_steps )
        
        expected_input_path = actual_file_path + '.tags.json'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            d = { 'file_data' : { 'tags' : rows } }
            
            j = json.dumps( d )
            
            f.write( j )
            
        
        parse_rules = [
            ( ClientParsing.JSON_PARSE_RULE_TYPE_DICT_KEY, ClientStrings.StringMatch( match_type = ClientStrings.STRING_MATCH_FIXED, match_value = 'file_data', example_string = 'file_data' ) ),
            ( ClientParsing.JSON_PARSE_RULE_TYPE_DICT_KEY, ClientStrings.StringMatch( match_type = ClientStrings.STRING_MATCH_FIXED, match_value = 'tags', example_string = 'tags' ) ),
            ( ClientParsing.JSON_PARSE_RULE_TYPE_ALL_ITEMS, None )
        ]
        
        json_parsing_formula = ClientParsing.ParseFormulaJSON( parse_rules = parse_rules, content_to_fetch = ClientParsing.JSON_CONTENT_STRING )
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterJSON( string_processor = string_processor, suffix = 'tags', json_parsing_formula = json_parsing_formula )
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertTrue( len( result ) > 0 )
        self.assertNotEqual( set( result ), set( rows ) )
        self.assertEqual( set( result ), set( string_processor.ProcessStrings( rows ) ) )
        
        # with filename remove ext and string conversion
        
        expected_input_path = os.path.join( TG.test_controller.db_dir, 'file.jpg'[1:].rsplit( '.', 1 )[0] ) + '.json'
        
        with open( expected_input_path, 'w', encoding = 'utf-8' ) as f:
            
            j = json.dumps( rows )
            
            f.write( j )
            
        
        importer = ClientMetadataMigrationImporters.SingleFileMetadataImporterJSON( remove_actual_filename_ext = True, filename_string_converter = ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) )
        
        result = importer.Import( actual_file_path )
        
        os.unlink( expected_input_path )
        
        self.assertEqual( set( result ), set( rows ) )
        
    

class TestSingleFileMetadataExporters( unittest.TestCase ):
    
    def test_media_tags( self ):
        
        hash = os.urandom( 32 )
        rows = [ 'character:samus aran', 'blonde hair' ]
        
        # no tags makes no write
        
        service_key = TG.test_controller.example_tag_repo_service_key
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaTags( service_key )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, [] )
        
        with self.assertRaises( Exception ):
            
            [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
            
        
        # simple local
        
        service_key = CC.DEFAULT_LOCAL_TAG_SERVICE_KEY
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaTags( service_key )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, rows )
        
        hashes = { hash }
        
        expected_content_update_package = ClientContentUpdates.ContentUpdatePackage.STATICCreateFromContentUpdates( service_key, [ ClientContentUpdates.ContentUpdate( HC.CONTENT_TYPE_MAPPINGS, HC.CONTENT_UPDATE_ADD, ( tag, hashes ) ) for tag in rows ] )
        
        [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
        
        HF.compare_content_update_packages( self, content_update_package, expected_content_update_package )
        
        # simple repo
        
        service_key = TG.test_controller.example_tag_repo_service_key
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaTags( service_key )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, rows )
        
        hashes = { hash }
        
        expected_content_update_package = ClientContentUpdates.ContentUpdatePackage.STATICCreateFromContentUpdates( service_key, [ ClientContentUpdates.ContentUpdate( HC.CONTENT_TYPE_MAPPINGS, HC.CONTENT_UPDATE_PEND, ( tag, hashes ) ) for tag in rows ] )
        
        [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
        
        HF.compare_content_update_packages( self, content_update_package, expected_content_update_package )
        
    
    def test_media_notes( self ):
        
        hash = os.urandom( 32 )
        notes = [ 'test: this is a test note', 'another test: this is a different\n\ntest note' ]
        
        # no notes makes no write
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaNotes()
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, [] )
        
        with self.assertRaises( Exception ):
            
            [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
            
        
        # simple
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaNotes()
        
        TG.test_controller.SetRead( 'media_result', HF.GetFakeMediaResult( hash ) )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, notes )
        
        content_updates = [ ClientContentUpdates.ContentUpdate( HC.CONTENT_TYPE_NOTES, HC.CONTENT_UPDATE_SET, ( hash, name, note ) ) for ( name, note ) in [ n.split( ': ', 1 ) for n in notes ] ]
        
        expected_content_update_package = ClientContentUpdates.ContentUpdatePackage.STATICCreateFromContentUpdates( CC.LOCAL_NOTES_SERVICE_KEY, content_updates )
        
        [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
        
        HF.compare_content_update_packages( self, content_update_package, expected_content_update_package )
        
        #
        
        forced_name = 'aaaa'
        notes = [ 'this is a test note without a name' ]
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaNotes( forced_name = forced_name )
        
        TG.test_controller.SetRead( 'media_result', HF.GetFakeMediaResult( hash ) )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, notes )
        
        content_updates = [ ClientContentUpdates.ContentUpdate( HC.CONTENT_TYPE_NOTES, HC.CONTENT_UPDATE_SET, ( hash, forced_name, notes[0] ) ) ]
        
        expected_content_update_package = ClientContentUpdates.ContentUpdatePackage.STATICCreateFromContentUpdates( CC.LOCAL_NOTES_SERVICE_KEY, content_updates )
        
        [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
        
        HF.compare_content_update_packages( self, content_update_package, expected_content_update_package )
        
    
    def test_media_urls( self ):
        
        hash = os.urandom( 32 )
        urls = [ 'https://site.com/123456', 'https://cdn5.st.com/file/123456' ]
        
        # no urls makes no write
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaURLs()
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, [] )
        
        with self.assertRaises( Exception ):
            
            [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
            
        
        # simple
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaURLs()
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, urls )
        
        expected_content_update_package = ClientContentUpdates.ContentUpdatePackage.STATICCreateFromContentUpdates( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, [ ClientContentUpdates.ContentUpdate( HC.CONTENT_TYPE_URLS, HC.CONTENT_UPDATE_ADD, ( urls, { hash } ) ) ] )
        
        [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
        
        HF.compare_content_update_packages( self, content_update_package, expected_content_update_package )
        
    
    def test_media_timestamps( self ):
        
        hash = os.urandom( 32 )
        timestamp = HydrusTime.GetNow() - 3600
        
        rows = [ str( timestamp ) ]
        
        # no timestamps makes no write
        
        timestamp_data_stub = ClientTime.TimestampData.STATICSimpleStub( HC.TIMESTAMP_TYPE_ARCHIVED )
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaTimestamps()
        
        exporter.SetTimestampDataStub( timestamp_data_stub )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, [] )
        
        with self.assertRaises( Exception ):
            
            [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
            
        
        # simple
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterMediaTimestamps()
        
        exporter.SetTimestampDataStub( timestamp_data_stub )
        
        TG.test_controller.ClearWrites( 'content_updates' )
        
        exporter.Export( hash, rows )
        
        expected_timestamp_data_result = ClientTime.TimestampData.STATICArchivedTime( timestamp * 1000 ) # no precise milliseconds because we do not read millisecond precision from metadata migration yet!
        
        expected_content_update_package = ClientContentUpdates.ContentUpdatePackage.STATICCreateFromContentUpdates( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, [ ClientContentUpdates.ContentUpdate( HC.CONTENT_TYPE_TIMESTAMP, HC.CONTENT_UPDATE_SET, ( ( hash, ), expected_timestamp_data_result ) ) ] )
        
        [ ( ( content_update_package, ), kwargs ) ] = TG.test_controller.GetWrite( 'content_updates' )
        
        HF.compare_content_update_packages( self, content_update_package, expected_content_update_package )
        
    
    def test_media_txt( self ):
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        rows = [ 'character:samus aran', 'blonde hair' ]
        
        # no rows makes no write
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT()
        
        exporter.Export( actual_file_path, [] )
        
        expected_output_path = actual_file_path + '.txt'
        
        self.assertFalse( os.path.exists( expected_output_path ) )
        
        # simple
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT()
        
        exporter.Export( actual_file_path, rows )
        
        expected_output_path = actual_file_path + '.txt'
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( HydrusText.DeserialiseNewlinedTexts( text ) ) )
        
        # with suffix
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT( suffix = 'tags' )
        
        exporter.Export( actual_file_path, rows )
        
        expected_output_path = actual_file_path + '.tags.txt'
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( HydrusText.DeserialiseNewlinedTexts( text ) ) )
        
        # diff separator
        
        separator = ', '
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT( suffix = 'tags', separator = separator )
        
        exporter.Export( actual_file_path, rows )
        
        expected_output_path = actual_file_path + '.tags.txt'
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( text.split( separator ) ) )
        
        # with filename remove ext and string conversion
        
        expected_output_path = os.path.join( TG.test_controller.db_dir, 'file.jpg'[1:].rsplit( '.', 1 )[0] ) + '.txt'
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterTXT( remove_actual_filename_ext = True, filename_string_converter = ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) )
        
        exporter.Export( actual_file_path, rows )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( HydrusText.DeserialiseNewlinedTexts( text ) ) )
        
    
    def test_media_json( self ):
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        rows = [ 'character:samus aran', 'blonde hair' ]
        
        # no rows makes no write
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterJSON()
        
        exporter.Export( actual_file_path, [] )
        
        expected_output_path = actual_file_path + '.json'
        
        self.assertFalse( os.path.exists( expected_output_path ) )
        
        # simple
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterJSON()
        
        exporter.Export( actual_file_path, rows )
        
        expected_output_path = actual_file_path + '.json'
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( json.loads( text ) ) )
        
        # with suffix and json dest
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterJSON( suffix = 'tags', nested_object_names = [ 'file_data', 'tags' ] )
        
        exporter.Export( actual_file_path, rows )
        
        expected_output_path = actual_file_path + '.tags.json'
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( json.loads( text )[ 'file_data' ][ 'tags' ] ) )
        
        # with filename remove ext and string conversion
        
        expected_output_path = os.path.join( TG.test_controller.db_dir, 'file.jpg'[1:].rsplit( '.', 1 )[0] ) + '.json'
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterJSON( remove_actual_filename_ext = True, filename_string_converter = ClientStrings.StringConverter( conversions = [ ( ClientStrings.STRING_CONVERSION_REMOVE_TEXT_FROM_BEGINNING, 1 ) ] ) )
        
        exporter.Export( actual_file_path, rows )
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( rows ), set( json.loads( text ) ) )
        
    
    def test_media_json_combined( self ):
        
        actual_file_path = os.path.join( TG.test_controller.db_dir, 'file.jpg' )
        
        #
        
        tag_rows = [ 'character:samus aran', 'blonde hair' ]
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterJSON( nested_object_names = [ 'file_data', 'tags' ] )
        
        exporter.Export( actual_file_path, tag_rows )
        
        #
        
        url_rows = [ 'https://site.com/123456' ]
        
        exporter = ClientMetadataMigrationExporters.SingleFileMetadataExporterJSON( nested_object_names = [ 'file_data', 'urls' ] )
        
        exporter.Export( actual_file_path, url_rows )
        
        #
        
        expected_output_path = actual_file_path + '.json'
        
        self.assertTrue( os.path.exists( expected_output_path ) )
        
        with open( expected_output_path, 'r', encoding = 'utf-8' ) as f:
            
            text = f.read()
            
        
        os.unlink( expected_output_path )
        
        self.assertEqual( set( tag_rows ), set( json.loads( text )[ 'file_data' ][ 'tags' ] ) )
        self.assertEqual( set( url_rows ), set( json.loads( text )[ 'file_data' ][ 'urls' ] ) )
        
    
