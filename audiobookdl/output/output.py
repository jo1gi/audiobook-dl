from audiobookdl import logging, AudiobookMetadata
from audiobookdl.exceptions import FailedCombining

import os
import shutil
import platform
import subprocess
from typing import Sequence, Mapping

LOCATION_DEFAULTS = {
    'album': 'NA',
    'artist': 'NA',
}

def gen_output_filename(booktitle: str, file: Mapping[str, str], template: str) -> str:
    """Generates an output filename based on different attributes of the
    file"""
    arguments = {**file, **{"booktitle": booktitle}}
    filename = template.format(**arguments)
    return _fix_output(filename)


def combine_audiofiles(filenames: Sequence[str], tmp_dir: str, output_path: str):
    """Combines the given audiofiles in `path` into a new file"""
    inputs = "|".join(filenames)
    subprocess.run(
        ["ffmpeg", "-i", f"concat:{inputs}", "-safe", "0", "-codec", "copy", output_path],
        capture_output=not logging.ffmpeg_output,
    )
    if not os.path.exists(output_path):
        raise FailedCombining
    shutil.rmtree(tmp_dir)


def can_copy_codec(input_format: str, output_format: str) -> bool:
    """
    Checks whether the codec can be copies to the new output

    :param input_format: Input file filetype
    :param output_format: Output file filetype
    :returns: True if the codec can be copied
    """
    # TODO Add better verification
    return output_format == "mkv" \
        or output_format == "mka" \
        or (input_format == "ts" and output_format == "mp3")


def convert_output(filenames: Sequence[str], output_format: str):
    """Converts a list of audio files into another format and return new
    files"""
    new_paths = []
    for old_path in filenames:
        path_without_ext, old_ext = os.path.splitext(old_path)
        new_path = f"{path_without_ext}.{output_format}"
        if not output_format == old_ext:
            if can_copy_codec(old_ext, output_format):
                subprocess.run(
                    ["ffmpeg", "-i", old_path, "-codec", "copy", new_path],
                    capture_output=not logging.ffmpeg_output
                )
            else:
                subprocess.run(
                    ["ffmpeg", "-i", old_path, new_path],
                    capture_output=not logging.ffmpeg_output
                )
            os.remove(old_path)
        new_paths.append(new_path)
    return new_paths


def gen_output_location(template: str, metadata: AudiobookMetadata, remove_chars: str) -> str:
    """
    Generates the location of the output based on attributes of the audiobook.

    :param template: Python string template audiobook metadata is put into
    :param metadata: Audiobook metadata,
    :param remove_chars: List of characters to be removed from the final path
    :returns: `template` with metadata inserted
    """
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
