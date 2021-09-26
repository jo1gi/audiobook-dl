from .utils import output
from .utils import logging
from .utils import metadata
import os
import shutil


def download(service, combine=False, output_template="{title}",
             output_format="mp3"):
    """Downloads audiobook from service object"""
    # Downloading audiobok info
    service.before()
    service.title = service.get_title()
    files = service.get_files()
    meta = service.get_metadata()
    output_dir = output.gen_output_location(
            output_template,
            service.title,
            meta)
    # Downloading audio files
    filenames = service.download_files(files, output_dir)
    # Single audiofile
    if combine or len(filenames) == 1:
        combined_audiobook(service, filenames, output_dir, output_format, meta)
    # Multiple audiofiles
    else:
        add_metadata_to_dir(service, filenames, output_dir, meta)


def combined_audiobook(service, filenames, output_dir, output_format, meta):
    """Combines audiobook into a single audio file and embeds metadata"""
    output_file = f"{output_dir}.{output_format}"
    if len(filenames) > 1:
        combine_files(service, filenames, output_dir, output_file)
    embed_metadata_in_file(service, meta, output_file)
    shutil.rmtree(output_dir)


def combine_files(service, filenames, output_dir, output_file):
    """Combines audiobook files and cleanes up afterward"""
    logging.log("Combining files")
    output.combine_audiofiles(filenames, output_dir, output_file)
    if not os.path.exists(output_file):
        logging.error("Could not combine audio files")
        exit()


def embed_metadata_in_file(service, meta, output_file):
    """Embed metadata into combined audiobook file"""
    if meta is not None:
        metadata.add_metadata(output_file, meta)
    cover = service.get_cover()
    if cover is not None:
        logging.log("Embedding cover")
        metadata.embed_cover(output_file, cover)
    chapters = service.get_chapters()
    if chapters is not None:
        logging.log("Adding chapters")
        metadata.add_chapters(output_file, chapters)


def add_metadata_to_dir(service, filenames, output_dir, meta):
    """Adds metadata to dir of audiobook files"""
    for i in filenames:
        metadata.add_metadata(os.path.join(output_dir, i), meta)
    cover = service.get_cover()
    if cover is not None:
        logging.log("Downloading cover")
        cover_path = os.path.join(
            output_dir,
            f"cover.{service.get_cover_filetype()}")
        with open(cover_path, 'wb') as f:
            f.write(cover)
