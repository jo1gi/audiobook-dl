from . import id3, mp4, ffmpeg
from audiobookdl import logging, Chapter, AudiobookMetadata, Cover
from audiobookdl.utils import program_in_path

import os
from typing import Sequence

def add_metadata(filepath: str, metadata: AudiobookMetadata):
    """Adds metadata to the given audio file"""
    if id3.is_id3_file(filepath):
        id3.add_id3_metadata(filepath, metadata)
    elif mp4.is_mp4_file(filepath):
        mp4.add_mp4_metadata(filepath, metadata)
    else:
        logging.debug("Could not add any metadata")


def embed_cover(filepath: str, cover: Cover):
    """Embeds an image into the given audio file"""
    if id3.is_id3_file(filepath):
        id3.embed_id3_cover(filepath, cover)
    elif mp4.is_mp4_file(filepath):
        mp4.embed_mp4_cover(filepath, cover)
    else:
        logging.debug("Could not embed cover")


def add_chapters(filepath: str, chapters: Sequence[Chapter]):
    """Adds chapters to the given audio file"""
    if id3.is_id3_file(filepath):
        id3.add_id3_chapters(filepath, chapters)
    elif program_in_path("ffmpeg"):
        ffmpeg.add_chapters_ffmpeg(filepath, chapters)
    else:
        if logging.debug_mode:
            logging.debug("Could not add chapters")
        else:
            filetype = os.path.splitext(filepath)[1][1:]
            logging.print_error_file("chapters_add", filetype=filetype)
