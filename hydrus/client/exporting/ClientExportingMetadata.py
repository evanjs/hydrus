import json
import os
import pathlib
import re
import typing
from typing import TextIO

from hydrus.core import HydrusConstants as HC
from hydrus.core import HydrusData
from hydrus.core import HydrusGlobals as HG
from hydrus.core import HydrusSerialisable
from hydrus.core import HydrusTags
from hydrus.core import HydrusText

from hydrus.client import ClientStrings
from hydrus.client.media import ClientMediaResult
from hydrus.client.metadata import ClientTags

# `\s+`: strip leading and trailing spaces from the raw negative prompt
insensitive_negative_prompt = re.compile(r"Negative prompt:\s+", re.IGNORECASE)

def GetSidecarPath( actual_file_path: str, suffix: str, file_extension: str ):
    
    path_components = [ actual_file_path ]
    
    if suffix != '':
        
        path_components.append( suffix )
        
    
    path_components.append( file_extension )
    
    return '.'.join( path_components )

def GetSidecarPathAlt(actual_file_path: str):
    final_path = pathlib.Path(actual_file_path)
    return final_path.with_suffix('.txt')

class SingleFileMetadataExporterMedia( object ):
    
    def Export( self, hash: bytes, rows: typing.Collection[ str ] ):
        
        raise NotImplementedError()
        
    

class SingleFileMetadataImporterMedia( object ):
    
    def Import( self, media_result: ClientMediaResult.MediaResult ):
        
        raise NotImplementedError()
        
    

class SingleFileMetadataExporterSidecar( object ):
    
    def Export( self, actual_file_path: str, rows: typing.Collection[ str ] ):
        
        raise NotImplementedError()
        
    

class SingleFileMetadataImporterSidecar( object ):
    
    def Import( self, actual_file_path: str ):
        
        raise NotImplementedError()
        
    

# TODO: add ToString and any other stuff here so this can all show itself prettily in a listbox
# 'I grab a .reversotags.txt sidecar and reverse the text and then send it as tags to my tags'

class SingleFileMetadataRouter( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_METADATA_SINGLE_FILE_ROUTER
    SERIALISABLE_NAME = 'Metadata Single File Converter'
    SERIALISABLE_VERSION = 1
    
    def __init__( self, importers = None, string_processor = None, exporter = None ):
        
        if importers is None:
            
            importers = []
            
        
        if string_processor is None:
            
            string_processor = ClientStrings.StringProcessor()
            
        
        if exporter is None:
            
            exporter = SingleFileMetadataImporterExporterTXT()
            
        
        HydrusSerialisable.SerialisableBase.__init__( self )
        
        self._importers = HydrusSerialisable.SerialisableList( importers )
        self._string_processor = string_processor
        self._exporter = exporter
        
    
    def _GetSerialisableInfo( self ):
        
        serialisable_importers = self._importers.GetSerialisableTuple()
        serialisable_string_processor = self._string_processor.GetSerialisableTuple()
        serialisable_exporter = self._exporter.GetSerialisableTuple()
        
        return ( serialisable_importers, serialisable_string_processor, serialisable_exporter )
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        ( serialisable_importers, serialisable_string_processor, serialisable_exporter ) = serialisable_info
        
        self._importers = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_importers )
        self._string_processor = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_string_processor )
        self._exporter = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_exporter )
        
    
    def GetExporter( self ):
        
        return self._exporter
        
    
    def GetImportedSidecarTexts( self, file_path: str, and_process_them = True ):
        
        rows = set()
        
        for importer in self._importers:
            
            if isinstance( importer, SingleFileMetadataImporterSidecar ):
                
                rows.update( importer.Import( file_path ) )
                
            else:
                
                raise Exception( 'This convertor does not import from a sidecar!' )
                
            
        
        rows = sorted( rows, key = HydrusTags.ConvertTagToSortable )
        
        if and_process_them:
            
            rows = self._string_processor.ProcessStrings( starting_strings = rows )
            
        
        return rows
        
    
    def GetImporters( self ):
        
        return self._importers
        
    
    def Work( self, media_result: ClientMediaResult.MediaResult, file_path: str ):
        
        rows = set()
        
        for importer in self._importers:
            
            if isinstance( importer, SingleFileMetadataImporterSidecar ):
                
                rows.update( importer.Import( file_path ) )
                
            elif isinstance( importer, SingleFileMetadataImporterMedia ):
                
                rows.update( importer.Import( media_result ) )
                
            else:
                
                raise Exception( 'Problem with importer object!' )
                
            
        
        rows = sorted( rows, key = HydrusTags.ConvertTagToSortable )
        
        rows = self._string_processor.ProcessStrings( starting_strings = rows )
        
        if len( rows ) == 0:
            
            return
            
        
        if isinstance( self._exporter, SingleFileMetadataExporterSidecar ):
            
            self._exporter.Export( file_path, rows )
            
        elif isinstance( self._exporter, SingleFileMetadataExporterMedia ):
            
            self._exporter.Export( media_result.GetHash(), rows )
            
        else:
            
            raise Exception( 'Problem with exporter object!' )
            
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_METADATA_SINGLE_FILE_ROUTER ] = SingleFileMetadataRouter

class SingleFileMetadataImporterExporterMediaTags( HydrusSerialisable.SerialisableBase, SingleFileMetadataExporterMedia, SingleFileMetadataImporterMedia ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_METADATA_SINGLE_FILE_IMPORTER_EXPORTER_MEDIA_TAGS
    SERIALISABLE_NAME = 'Metadata Single File Importer Exporter Media Tags'
    SERIALISABLE_VERSION = 1
    
    def __init__( self, service_key = None ):
        
        HydrusSerialisable.SerialisableBase.__init__( self )
        SingleFileMetadataExporterMedia.__init__( self )
        SingleFileMetadataImporterMedia.__init__( self )
        
        self._service_key = service_key
        
    
    def _GetSerialisableInfo( self ):
        
        return self._service_key.hex()
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        serialisable_service_key = serialisable_info
        
        self._service_key = bytes.fromhex( serialisable_service_key )
        
    
    def GetServiceKey( self ) -> bytes:
        
        return self._service_key
        
    
    def Import( self, media_result: ClientMediaResult.MediaResult ):
        
        tags = media_result.GetTagsManager().GetCurrent( self._service_key, ClientTags.TAG_DISPLAY_STORAGE )
        
        return tags
        
    
    def Export( self, hash: bytes, rows: typing.Collection[ str ] ):
        
        if HG.client_controller.services_manager.GetServiceType( self._service_key ) == HC.LOCAL_TAG:
            
            add_content_action = HC.CONTENT_UPDATE_ADD
            
        else:
            
            add_content_action = HC.CONTENT_UPDATE_PEND
            
        
        hashes = { hash }
        
        content_updates = [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_MAPPINGS, add_content_action, ( tag, hashes ) ) for tag in rows ]
        
        HG.client_controller.WriteSynchronous( 'content_updates', { self._service_key : content_updates } )
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_METADATA_SINGLE_FILE_IMPORTER_EXPORTER_MEDIA_TAGS ] = SingleFileMetadataImporterExporterMediaTags


def handle_sd_metadata_path(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw_text = handle_sd_metadata_text_io(f)

    except Exception as e:
        raise Exception('Could not import SD metadata from {}: {}'.format(path, str(e)))

    rows = HydrusText.DeserialiseNewlinedTexts(raw_text)
    return rows

def handle_sd_metadata_text_io(textio: TextIO):
    all_lines = textio.read().splitlines()
    prompt_tags = [f"positive: {p.strip()}" for p in all_lines[0].split(",")]
    only_negative_tags = [nt.strip() for nt in all_lines[1].replace("Negative prompt: ", "").split(",")]
    negative_tags = [f"negative: {n}" for n in only_negative_tags]

    settings = all_lines[2].split(",")
    all_tags = []
    all_tags.extend(prompt_tags)
    all_tags.extend(negative_tags)
    all_tags.extend(settings)
    raw_text = os.linesep.join(all_tags)
    return raw_text


def handle_sd_metadata_text(all_lines: str):
    lines = all_lines.split("\n")
    all_tags = []

    prompt_tags = [f"positive: {p.strip()}" for p in lines[0].split(",")]
    all_tags.extend(prompt_tags)

    maybe_negative = list([line for line in lines if str(line).startswith("Negative")])
    if len(maybe_negative) > 0:
        negative_prompt = maybe_negative[0]
        only_negative_tags = [nt.strip() for nt in negative_prompt.replace("Negative prompt: ", "").split(",")]
        negative_tags = [f"negative: {n}" for n in only_negative_tags]
        all_tags.extend(negative_tags)

    maybe_settings = list([line for line in lines if str(line).startswith("Steps")])
    if len(maybe_settings) > 0:
        settings = maybe_settings[0].split(", ")
        all_tags.extend(settings)

    raw_text = os.linesep.join(all_tags)
    return raw_text

def handle_sd_prompts_text(all_lines: str) -> dict:
    notes = {}
    lines = all_lines.split("\n")
    notes["prompt"] = lines[0].strip()
    maybe_negative = list([line for line in lines if str(line).startswith("Negative")])
    if len(maybe_negative) > 0:
        negative_prompt = maybe_negative[0].strip()
        # Remove the "Negative prompt:" string from the start of the prompt string
        notes["negative prompt"] = insensitive_negative_prompt.sub("", negative_prompt)

    return notes

def handle_sd_novelai_prompts_text(data) -> dict:
    description = data['Description']
    prompt = description
    comment = data['Comment']
    parameters = json.loads(comment)
    negative_prompt = parameters['uc']

    return {"prompt": prompt, "negative prompt": negative_prompt}

def handle_sd_novelai_metadata_text(data):
    title = data['Title']
    description = data['Description']
    comment = data['Comment']
    parameters = json.loads(comment)
    prompt_tags = [f"positive: {p.strip()}" for p in description.split(",") if len(p) > 0]
    negative_tags = [f"negative: {n.strip()}" for n in parameters['uc'].split(',') if len(n) > 0]

    all_tags = []
    all_tags.extend(prompt_tags)
    all_tags.extend(negative_tags)

    settings = []
    settings.append(f"title: {title}")
    settings.append(f"denoising strength: {parameters['strength']}")
    settings.append(f"steps: {parameters['steps']}")
    settings.append(f"seed: {parameters['seed']}")
    settings.append(f"cfg scale: {parameters['scale']}")
    settings.append(f"noise: {parameters['noise']}")
    settings.append(f"sampler: {parameters['sampler']}")
    all_tags.extend(settings)

    return all_tags


class SingleFileMetadataImporterExporterTXT( HydrusSerialisable.SerialisableBase, SingleFileMetadataExporterSidecar, SingleFileMetadataImporterSidecar ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_METADATA_SINGLE_FILE_IMPORTER_EXPORTER_TXT
    SERIALISABLE_NAME = 'Metadata Single File Importer Exporter TXT'
    SERIALISABLE_VERSION = 1
    
    def __init__( self, suffix = None ):
        
        HydrusSerialisable.SerialisableBase.__init__( self )
        SingleFileMetadataExporterSidecar.__init__( self )
        SingleFileMetadataImporterSidecar.__init__( self )
        
        if suffix is None:
            
            suffix = ''
            
        
        self._suffix = suffix
        
    
    def _GetSerialisableInfo( self ):
        
        return self._suffix
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        self._suffix = serialisable_info
        
    
    def Export( self, actual_file_path: str, rows: typing.Collection[ str ] ):
        
        path = GetSidecarPath( actual_file_path, self._suffix, 'txt' )
        
        with open( path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( '\n'.join( rows ) )
            
        
    
    def Import( self, actual_file_path: str ) -> typing.Collection[ str ]:
        standard_path = GetSidecarPath(actual_file_path, self._suffix, 'txt')
        path_alt = GetSidecarPathAlt(actual_file_path)
        if os.path.exists(path_alt):
            return handle_sd_metadata_path(path_alt)
        elif os.path.exists(standard_path):
            path = standard_path
        else:
            return []
            
        
        try:
            
            with open( path, 'r', encoding = 'utf-8' ) as f:
                
                raw_text = f.read()
                
            
        except Exception as e:
            
            raise Exception( 'Could not import from {}: {}'.format( path, str( e ) ) )
            
        
        rows = HydrusText.DeserialiseNewlinedTexts( raw_text )
        
        return rows
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_METADATA_SINGLE_FILE_IMPORTER_EXPORTER_TXT ] = SingleFileMetadataImporterExporterTXT
