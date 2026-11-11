from . import id3, mp4, ffmpeg
from audiobookdl import logging, Chapter, AudiobookMetadata, Cover
from audiobookdl.utils import program_in_path

import os
from io import BytesIO
from typing import Sequence

from PIL import Image

def add_metadata(filepath: str, metadata: AudiobookMetadata):
    """Adds metadata to the given audio file"""
    if id3.is_id3_file(filepath):
        id3.add_id3_metadata(filepath, metadata)
    elif mp4.is_mp4_file(filepath):
        mp4.add_mp4_metadata(filepath, metadata)
    else:
        logging.debug("Could not add any metadata")


def _normalize_cover(cover: Cover) -> Cover:
    """Re-encode cover art to JPEG unless it is already JPEG/PNG. Some sources
    (e.g. Nextory) serve WebP but label it "jpg", which players can't decode."""
    try:
        image = Image.open(BytesIO(cover.image))
        fmt = (image.format or "").lower()
    except Exception:
        return cover
    if fmt == "jpeg":
        return Cover(cover.image, "jpg")
    if fmt == "png":
        return Cover(cover.image, "png")
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=90)
    return Cover(buffer.getvalue(), "jpg")


def embed_cover(filepath: str, cover: Cover):
    """Embeds an image into the given audio file"""
    cover = _normalize_cover(cover)
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
