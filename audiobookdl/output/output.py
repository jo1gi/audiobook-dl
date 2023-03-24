from audiobookdl import logging, AudiobookMetadata
from audiobookdl.exceptions import FailedCombining

import os
import shutil
import platform
import subprocess

LOCATION_DEFAULTS = {
    'album': 'NA',
    'artist': 'NA',
}

def gen_output_filename(booktitle: str, file: dict[str, str], template: str) -> str:
    """Generates an output filename based on different attributes of the
    file"""
    arguments = {**file, **{"booktitle": booktitle}}
    filename = template.format(**arguments)
    return _fix_output(filename)


def combine_audiofiles(filenames: list[str], tmp_dir: str, output_path: str):
    """Combines the given audiofiles in `path` into a new file"""
    inputs = "|".join(filenames)
    subprocess.run(
        ["ffmpeg", "-i", f"concat:{inputs}", "-safe", "0", "-c", "copy", output_path],
        capture_output=not logging.ffmpeg_output,
    )
    if not os.path.exists(output_path):
        raise FailedCombining
    shutil.rmtree(tmp_dir)


def convert_output(filenames: list[str], output_format: str):
    """Converts a list of audio files into another format and return new
    files"""
    new_paths = []
    for old_path in filenames:
        split_path = os.path.splitext(old_path)
        new_path = f"{split_path[0]}.{output_format}"
        if not output_format == split_path[1][1:]:
            subprocess.run(
                ["ffmpeg", "-i", old_path, new_path],
                capture_output=not logging.ffmpeg_output
            )
            os.remove(old_path)
        new_paths.append(f"{os.path.splitext(old_path)[0]}.{output_format}")
    return new_paths


def gen_output_location(template: str, metadata: AudiobookMetadata, remove_chars: str) -> str:
    """Generates the location of the output based on attributes of the
    audiobook"""
    if metadata is None:
        metadata = {}
    metadata.title = _fix_output(metadata.title)
    metadata_dict = {**LOCATION_DEFAULTS, **metadata.all_properties_dict()}
    formatted = template.format(**metadata_dict)
    formatted = _remove_chars(formatted, remove_chars)
    return formatted


def _fix_output(title: str) -> str:
    """Returns title without characters system can't handle"""
    title = title.replace("/", "-")
    if platform.system() == "Windows":
        title = _remove_chars(title, ':*\\?<>|"\'’')
    return title


def _remove_chars(s: str, chars: str) -> str:
    """Removes `chars` from `s`"""
    for i in chars:
        s = s.replace(i, "")
    return s
