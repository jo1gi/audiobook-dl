from audiobookdl import AudiobookFile, Source, logging
from audiobookdl.exceptions import UserNotAuthorized, NoFilesFound, FailedCombining
from . import metadata, output, encryption

import os
import shutil
from functools import partial
from typing import Any
from rich.progress import Progress, BarColumn, ProgressColumn
from rich.prompt import Confirm
from multiprocessing.pool import ThreadPool

DOWNLOAD_PROGRESS: list[str | ProgressColumn] = [
    "{task.description}", BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%"
]


def download(source: Source, options):
    """Downloads audiobook from source object"""
    # Downloading audiobook info
    if source.requires_authentication and not source.authenticated:
        raise UserNotAuthorized
    logging.log("Downloading metadata")
    source.before()
    files = source.get_files()
    if len(files) == 0:
        raise NoFilesFound
    output_dir = output.gen_output_location(
            options.output_template,
            source.metadata())
    # Downloading audio files
    filenames = download_files_output(source, files, output_dir)
    # Finding output format
    if options.output_format:
        output_format = options.output_format
    else:
        output_format = os.path.splitext(filenames[0])[1][1:]
        if output_format == "ts":
            output_format = "mp3"
    # Converting audio files to specified format
    logging.log("Converting files")
    filenames = output.convert_output(filenames, output_dir, output_format)
    # Single audiofile
    if options.combine or len(filenames) == 1:
        combined_audiobook(source, filenames, output_dir, output_format, options)
    # Multiple audiofiles
    else:
        add_metadata_to_dir(source, filenames, output_dir)

def setup_download_dir(path: str):
    """Creates output folder"""
    if os.path.isdir(path):
        answer = Confirm.ask(f"The folder '{path}' already exists. Do you want to override it?")
        if answer:
            shutil.rmtree(path)
        else:
            exit()
    os.makedirs(path)

def download_files_output(
        source: Source,
        files: list[AudiobookFile],
        output_dir: str
    ) -> list[str]:
    """Download `files` with progress bar in terminal"""
    setup_download_dir(output_dir)
    with logging.progress(DOWNLOAD_PROGRESS) as progress:
        task = progress.add_task(
            f"Downloading {len(files)} files - [blue]{source.get_title()}",
            total = len(files)
        )
        # Function for updating progress bar
        p = partial(progress.advance, task)
        # List of new filenames
        filenames = download_files(source, p, files, output_dir)
        remaining: float = progress.tasks[0].remaining or 0
        progress.advance(task, remaining)
        return filenames


def create_filename(
        title: str,
        length: int,
        index: int,
        output_dir: str,
        file: AudiobookFile,
    ) -> tuple[str, str]:
    """Create filename of audiobook file"""
    if length == 1:
        name = f"{title}.{file.ext}"
        path = f"{output_dir}.{file.ext}"
    else:
        name = f"{title} - Part {index}.{file.ext}"
        path = os.path.join(output_dir, name)
    return name, path

def download_file(args: tuple[AudiobookFile, int, int, str, Any, Source]):
    # Setting up variables
    file, length, index, output_dir, progress, source = args
    logging.debug(f"Starting downloading file: {file.url}")
    name, path = create_filename(source.get_title(), length, index, output_dir, file)
    req = source._session.get(file.url, headers=file.headers, stream=True)
    file_size = int(req.headers["Content-length"])
    total: float = 0
    # Downloading file
    with open(path, "wb") as f:
        for chunk in req.iter_content(chunk_size=1024):
            f.write(chunk)
            new = len(chunk)/file_size
            total += new
            progress(new)
    progress(1-total)
    # Decrypting file if necessary
    if file.encryption_method:
        encryption.decrypt_file(path, file.encryption_method)
    return name


def download_files(
        source: Source,
        update,
        files: list[AudiobookFile],
        output_dir: str
    ) -> list[str]:
    """Downloads and saves audiobook files to disk"""
    filenames = []
    with ThreadPool(processes=20) as pool:
        arguments = []
        for n, f in enumerate(files):
            arguments.append((f, len(files), n+1, output_dir, update, source))
        for i in pool.imap(download_file, arguments):
            filenames.append(i)
    return filenames

def combined_audiobook(source: Source,
                       filenames: list[str],
                       output_dir: str,
                       output_format: str,
                       options):
    """Combines audiobook into a single audio file and embeds metadata"""
    # Combining files
    output_file = f"{output_dir}.{output_format}"
    if len(filenames) > 1:
        logging.log("Combining files")
        output.combine_audiofiles(filenames, output_dir, output_file)
        if not os.path.exists(output_file):
            raise FailedCombining
    # Adding metadata
    embed_metadata_in_file(source, output_file, options)
    shutil.rmtree(output_dir)


def embed_metadata_in_file(source: Source, output_file: str, options):
    """Embed metadata into combined audiobook file"""
    if source.metadata is not None:
        metadata.add_metadata(output_file, source.metadata())
    cover = source.get_cover()
    if cover is not None:
        logging.log("Embedding cover")
        metadata.embed_cover(output_file, cover, source.get_cover_extension())
    chapters = source.get_chapters()
    if chapters is not None and not options.no_chapters:
        logging.log("Adding chapters")
        metadata.add_chapters(output_file, chapters)


def add_metadata_to_dir(source: Source, filenames: list[str], output_dir: str):
    """Adds metadata to dir of audiobook files"""
    for i in filenames:
        metadata.add_metadata(os.path.join(output_dir, i), source.metadata())
    cover = source.get_cover()
    if cover is not None:
        logging.log("Downloading cover")
        cover_path = os.path.join(
            output_dir,
            f"cover.{source.get_cover_extension()}")
        with open(cover_path, 'wb') as f:
            f.write(cover)
