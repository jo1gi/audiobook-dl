import os
import platform
from pydub import AudioSegment
from typing import List, Dict


LOCATION_DEFAULTS = {
        'album': 'NA',
        'artist': 'NA',
        }

def gen_output_filename(booktitle: str, file: Dict[str, str], template: str) -> str:
    """Generates an output filename based on different attributes of the
    file"""
    arguments = {**file, **{"booktitle": booktitle}}
    filename = template.format(**arguments)
    return fix_output(filename)

def combine_audiofiles(filenames: List[str], tmp_dir: str, output_path: str):
    """Combines the given audiofiles in `path` into a new file"""
    combined: AudioSegment = AudioSegment.from_file(os.path.join(tmp_dir, filenames[0]))
    for f in filenames[1:]:
        path = os.path.join(tmp_dir, f)
        combined.append(AudioSegment.from_file(path))
    combined.export(output_path)


def convert_output(filenames: List[str], output_dir: str, output_format: str):
    """Converts a list of audio files into another format and return new
    files"""
    new_paths = []
    for name in filenames:
        full_path = os.path.join(output_dir, name)
        split_path = os.path.splitext(full_path)
        new_path = f"{split_path[0]}.{output_format}"
        if not output_format == split_path[1][1:]:
            audio: AudioSegment = AudioSegment.from_file(full_path)
            audio.export(new_path, format=output_format)
        new_paths.append(f"{os.path.splitext(name)[0]}.{output_format}")
    return new_paths


def gen_output_location(template: str, metadata: Dict[str, str]) -> str:
    """Generates the location of the output based on attributes of the
    audiobook"""
    if metadata is None:
        metadata = {}
    metadata["title"] = fix_output(metadata["title"])
    metadata = {**LOCATION_DEFAULTS, **metadata}
    return template.format(**metadata)


def fix_output(title: str) -> str:
    """Returns title without characters system can't handle"""
    title = title.replace("/", "-")
    if platform.system() == "Windows":
        title = remove_chars(title, ':*\\?<>|"\'’')
    return title


def remove_chars(s: str, chars: str) -> str:
    """Removes `chars` from `s`"""
    for i in chars:
        s = s.replace(i, "")
    return s
