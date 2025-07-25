import os
import shutil
import time
import unittest

from hydrus.core import HydrusGlobals as HG
from hydrus.core import HydrusPaths
from hydrus.core import HydrusStaticDir
from hydrus.core import HydrusTemp

from hydrus.client import ClientConstants as CC
from hydrus.client.importing import ClientImportFiles
from hydrus.client.importing import ClientImportLocal

from hydrus.test import TestGlobals as TG

with open( HydrusStaticDir.GetStaticPath( 'hydrus.png' ), 'rb' ) as f:
    
    EXAMPLE_FILE = f.read()
    

class TestDaemons( unittest.TestCase ):
    
    def test_import_folders_daemon( self ):
        
        test_dir = HydrusTemp.GetSubTempDir( 'import_test' )
        
        try:
            
            TG.test_controller.SetRead( 'hash_status', ClientImportFiles.FileImportStatus.STATICGetUnknownStatus() )
            
            HydrusPaths.MakeSureDirectoryExists( test_dir )
            
            hydrus_png_path = HydrusStaticDir.GetStaticPath( 'hydrus.png' )
            
            HydrusPaths.MirrorFile( hydrus_png_path, os.path.join( test_dir, '0' ) )
            HydrusPaths.MirrorFile( hydrus_png_path, os.path.join( test_dir, '1' ) ) # previously imported
            HydrusPaths.MirrorFile( hydrus_png_path, os.path.join( test_dir, '2' ) )
            
            with open( os.path.join( test_dir, '3' ), 'wb' ) as f: f.write( b'blarg' ) # broken
            with open( os.path.join( test_dir, '4' ), 'wb' ) as f: f.write( b'blarg' ) # previously failed
            
            #
            
            actions = {}
            
            actions[ CC.STATUS_SUCCESSFUL_AND_NEW ] = CC.IMPORT_FOLDER_DELETE
            actions[ CC.STATUS_SUCCESSFUL_BUT_REDUNDANT ] = CC.IMPORT_FOLDER_DELETE
            actions[ CC.STATUS_DELETED ] = CC.IMPORT_FOLDER_DELETE
            actions[ CC.STATUS_ERROR ] = CC.IMPORT_FOLDER_IGNORE
            
            import_folder = ClientImportLocal.ImportFolder( 'imp', path = test_dir, actions = actions )
            
            TG.test_controller.SetRead( 'serialisable_names', [ 'imp' ] )
            TG.test_controller.SetRead( 'serialisable_named', import_folder )
            
            TG.test_controller.ClearWrites( 'import_file' )
            TG.test_controller.ClearWrites( 'serialisable' )
            
            manager = ClientImportLocal.ImportFoldersManager( HG.controller )
            
            manager.Start()
            
            manager.Wake()
            
            time.sleep( 3 )
            
            for i in range( 10 ):
                
                if HG.import_folders_running:
                    
                    time.sleep( 1 )
                    
                
            
            try:
                
                import_file = TG.test_controller.GetWrite( 'import_file' )
                
                # let's check that three files were imported; local importers do not do pre-import metadata stuff to skip work, so this will be three actual db jobs
                self.assertEqual( len( import_file ), 3 )
                
                # I need to expand tests here with the new file system
                
                [ ( ( updated_import_folder, ), empty_dict ) ] = TG.test_controller.GetWrite( 'serialisable' )
                
                self.assertEqual( updated_import_folder, import_folder )
                
                self.assertTrue( not os.path.exists( os.path.join( test_dir, '0' ) ) )
                self.assertTrue( not os.path.exists( os.path.join( test_dir, '1' ) ) )
                self.assertTrue( not os.path.exists( os.path.join( test_dir, '2' ) ) )
                self.assertTrue( os.path.exists( os.path.join( test_dir, '3' ) ) )
                self.assertTrue( os.path.exists( os.path.join( test_dir, '4' ) ) )
                
            finally:
                
                manager.Shutdown()
                
            
        finally:
            
            shutil.rmtree( test_dir )
            
        
    
