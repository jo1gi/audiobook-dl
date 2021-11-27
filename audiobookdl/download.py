from .utils import output
from .utils import logging
from .utils import metadata
from .utils.exceptions import UserNotAuthenticated
import os
import shutil
from typing import Dict, List


def download(source,
             combine: bool = False,
             output_template: str = "{title}",
             output_format: str = "mp3"):
    """Downloads audiobook from source object"""
    # Downloading audiobook info
    if source.require_cookies and not source._cookies_loaded:
        raise UserNotAuthenticated
    source.before()
    source.title = source.get_title()
    files = source.get_files()
    meta = source.get_metadata()
    output_dir = output.gen_output_location(
            output_template,
            source.title,
            meta)
    # Downloading audio files
    filenames = source.download_files(files, output_dir)
    # Single audiofile
    if combine or len(filenames) == 1:
        combined_audiobook(source, filenames, output_dir, output_format, meta)
    # Multiple audiofiles
    else:
        add_metadata_to_dir(source, filenames, output_dir, meta)


def combined_audiobook(source,
                       filenames: List[str],
                       output_dir: str,
                       output_format: str,
                       meta: Dict[str, str]):
    """Combines audiobook into a single audio file and embeds metadata"""
    output_file = f"{output_dir}.{output_format}"
    if len(filenames) > 1:
        combine_files(source, filenames, output_dir, output_file)
    embed_metadata_in_file(source, meta, output_file)
    shutil.rmtree(output_dir)


def combine_files(source,
                  filenames: List[str],
                  output_dir: str,
                  output_file: str):
    """Combines audiobook files and cleanes up afterward"""
    logging.log("Combining files")
    output.combine_audiofiles(filenames, output_dir, output_file)
    if not os.path.exists(output_file):
        logging.error("Could not combine audio files")
        exit()


def embed_metadata_in_file(source,
                           meta: Dict[str, str],
                           output_file: str):
    """Embed metadata into combined audiobook file"""
    if meta is not None:
        metadata.add_metadata(output_file, meta)
    cover = source.get_cover()
    if cover is not None:
        logging.log("Embedding cover")
        metadata.embed_cover(output_file, cover, source.get_cover_extension())
    chapters = source.get_chapters()
    if chapters is not None:
        logging.log("Adding chapters")
        metadata.add_chapters(output_file, chapters)


def add_metadata_to_dir(source,
                        filenames: List[str],
                        output_dir: str,
                        meta: Dict[str, str]):
    """Adds metadata to dir of audiobook files"""
    for i in filenames:
        metadata.add_metadata(os.path.join(output_dir, i), meta)
    cover = source.get_cover()
    if cover is not None:
        logging.log("Downloading cover")
        cover_path = os.path.join(
            output_dir,
            f"cover.{source.get_cover_extension()}")
        with open(cover_path, 'wb') as f:
            f.write(cover)
