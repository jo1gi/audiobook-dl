from .utils import output
from .utils import logging
from .utils import metadata
from .utils.source import Source
from .utils.exceptions import MissingCookies, NoFilesFound, FailedCombining
import os
import shutil
from typing import List, Optional


def download(source: Source, options):
    """Downloads audiobook from source object"""
    # Downloading audiobook info
    if source.require_cookies and not source._cookies_loaded:
        raise MissingCookies
    logging.log("Downloading metadata")
    source.before()
    files = source.get_files()
    if len(files) == 0:
        raise NoFilesFound
    output_dir = output.gen_output_location(
            options.output_template,
            source.metadata)
    # Downloading audio files
    filenames = source.download_files(files, output_dir)
    # Finding output format
    if options.output_format:
        output_format = options.output_format
    else:
        output_format = os.path.splitext(filenames[0])[1][1:]
        if output_format == "ts":
            output_format = "mp3"
    # Single audiofile
    if options.combine or len(filenames) == 1:
        combined_audiobook(source, filenames, output_dir, output_format, options)
    # Multiple audiofiles
    else:
        # Converting audio files to specified format
        logging.log("Converting files")
        filenames = output.convert_output(filenames, output_dir, output_format)
        # Adding metadata to the files
        add_metadata_to_dir(source, filenames, output_dir)


def combined_audiobook(source: Source,
                       filenames: List[str],
                       output_dir: str,
                       output_format: Optional[str],
                       options):
    """Combines audiobook into a single audio file and embeds metadata"""
    output_file = f"{output_dir}.{output_format}"
    if len(filenames) > 1:
        combine_files(filenames, output_dir, output_file)
    embed_metadata_in_file(source, output_file, options)
    shutil.rmtree(output_dir)


def combine_files(filenames: List[str], output_dir: str, output_file: str):
    """Combines audiobook files and cleanes up afterward"""
    logging.log("Combining files")
    output.combine_audiofiles(filenames, output_dir, output_file)
    if not os.path.exists(output_file):
        raise FailedCombining


def embed_metadata_in_file(source: Source, output_file: str, options):
    """Embed metadata into combined audiobook file"""
    if source.metadata is not None:
        metadata.add_metadata(output_file, source.metadata)
    cover = source.get_cover()
    if cover is not None:
        logging.log("Embedding cover")
        metadata.embed_cover(output_file, cover, source.get_cover_extension())
    chapters = source.get_chapters()
    if chapters is not None and not options.no_chapters:
        logging.log("Adding chapters")
        metadata.add_chapters(output_file, chapters)


def add_metadata_to_dir(source: Source,
                        filenames: List[str],
                        output_dir: str):
    """Adds metadata to dir of audiobook files"""
    for i in filenames:
        metadata.add_metadata(os.path.join(output_dir, i), source.metadata)
    cover = source.get_cover()
    if cover is not None:
        logging.log("Downloading cover")
        cover_path = os.path.join(
            output_dir,
            f"cover.{source.get_cover_extension()}")
        with open(cover_path, 'wb') as f:
            f.write(cover)
