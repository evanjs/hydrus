import json
import os
import pathlib
import re
import typing

from hydrus.core import HydrusTags, HydrusText

# `\s+`: strip leading and trailing spaces from the raw negative prompt
insensitive_negative_prompt = re.compile(r"Negative prompt:\s+", re.IGNORECASE)

def get_tags_from_metadata(params):
    tag_dict = {}
    if isinstance(params, str):
        parsed_tags = handle_sd_metadata_text(params)
        if parsed_tags is not None:
            clean_tags = list([x for x in HydrusTags.CleanTags(parsed_tags.splitlines())])
            tag_dict = dict(zip(iter(clean_tags), iter(clean_tags)))
    elif isinstance(params, dict):
        parsed_tags = handle_sd_novelai_metadata_text(params)
        if parsed_tags is not None:
            clean_tags = list([x for x in HydrusTags.CleanTags(parsed_tags)])
            tag_dict = dict(zip(iter(clean_tags), iter(clean_tags)))
    return tag_dict

def get_notes_from_metadata(params):
    prompts_dict = {}
    if isinstance(params, str):
        parsed_prompts = handle_sd_prompts_text(params)
        if parsed_prompts is not None:
            prompts_dict = parsed_prompts
    elif isinstance(params, dict):
        parsed_prompts = handle_sd_novelai_prompts_text(params)
        if parsed_prompts is not None:
            prompts_dict = parsed_prompts
    return prompts_dict

def GetSidecarPath( actual_file_path: str, suffix: str, file_extension: str ):
    
    path_components = [ actual_file_path ]
    
    if suffix != '':
        
        path_components.append( suffix )
        
    
    path_components.append( file_extension )
    
    return '.'.join( path_components )
    
def GetSidecarPathAlt(actual_file_path: str):
    final_path = pathlib.Path(actual_file_path)
    return final_path.with_suffix('.txt')

class ImporterExporterNode( object ):
    
    def __str__( self ):
        
        return self.ToString()
        
    
    def GetExampleStrings( self ):
        
        examples = [
            'blue eyes',
            'blonde hair',
            'skirt',
            'character:jane smith',
            'series:jane smith adventures',
            'creator:some guy',
            'https://example.com/gallery/index.php?post=123456&page=show',
            'https://cdn3.expl.com/files/file_id?id=123456&token=0123456789abcdef'
        ]
        
        return examples
        
    
    def ToString( self ) -> str:
        
        raise NotImplementedError()
        
    

class SidecarNode( object ):
    
    def __init__( self, suffix: str ):
        
        self._suffix = suffix
        
    
    def GetSuffix( self ) -> str:
        
        return self._suffix
        
    
    def SetSuffix( self, suffix: str ):
        
        self._suffix = suffix
        
    

def handle_sd_metadata_path(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw_text = handle_sd_metadata_text_io(f)

    except Exception as e:
        raise Exception('Could not import SD metadata from {}: {}'.format(path, str(e)))

    rows = HydrusText.DeserialiseNewlinedTexts(raw_text)
    return rows

def handle_sd_metadata_text_io(textio: typing.TextIO):
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
