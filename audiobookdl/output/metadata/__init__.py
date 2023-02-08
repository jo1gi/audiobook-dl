from audiobookdl import logging, Chapter
from . import id3, mp4

def add_metadata(filepath: str, metadata: dict[str, str]):
    """Adds metadata to the given audio file"""
    if id3.is_id3_file(filepath):
        id3.add_id3_metadata(filepath, metadata)
    elif mp4.is_mp4_file(filepath):
        mp4.add_mp4_metadata(filepath, metadata)
    else:
        logging.debug("Could not add any metadata")


def embed_cover(filepath: str, image: bytes, extension: str):
    """Embeds an image into the given audio file"""
    if id3.is_id3_file(filepath):
        id3.embed_id3_cover(filepath, image, extension)
    elif mp4.is_mp4_file(filepath):
        mp4.embed_mp4_cover(filepath, image, extension)
    else:
        logging.debug("Could not embed cover")


def add_chapters(filepath: str, chapters: list[Chapter]):
    """Adds chapters to the given audio file"""
    if id3.is_id3_file(filepath):
        id3.add_id3_chapters(filepath, chapters)
    else:
        logging.debug("Could not add chapters")
