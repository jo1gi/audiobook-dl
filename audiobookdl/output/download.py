from audiobookdl import AudiobookFile, Source, logging, Audiobook
from audiobookdl.exceptions import UserNotAuthorized, NoFilesFound
from . import metadata, output, encryption

import os
import shutil
from functools import partial
from typing import Any, Union, Optional
from rich.progress import Progress, BarColumn, ProgressColumn
from rich.prompt import Confirm
from multiprocessing.pool import ThreadPool


DOWNLOAD_PROGRESS: list[Union[str, ProgressColumn]] = [
    "{task.description}", BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%"
]


def download(source: Source, options):
    """Downloads audiobook from source object"""
    try:
        audiobook = create_audiobook(source)
        output_dir = output.gen_output_location(options.output_template, audiobook.metadata, options.remove_chars)
        download_audiobook(audiobook, output_dir, options)
    except KeyboardInterrupt:
        logging.log("Stopped download")
        logging.log("Cleaning up files")
        shutil.rmtree(output_dir)


def create_audiobook(source: Source) -> Audiobook:
    """Creates a new `Audiobook` object from a `Source`"""
    if source.requires_authentication and not source.authenticated:
        raise UserNotAuthorized
    source.prepare()
    files = source.get_files()
    if len(files) == 0:
        raise NoFilesFound
    return Audiobook(
        session = source._session,
        metadata = source.get_metadata(),
        chapters = source.get_chapters(),
        files = files,
        cover = source.get_cover()
    )


def download_audiobook(audiobook: Audiobook, output_dir: str, options):
    """Download, convert, combine, and add metadata to files from `Audiobook` object"""
    # Downloading files
    filepaths = download_files_with_cli_output(audiobook, output_dir)
    # Converting files
    current_format, output_format = get_output_audio_format(options.output_format, filepaths)
    if current_format != output_format:
        logging.log("Converting files")
        filepaths = output.convert_output(filepaths, output_format)
    # Combine files
    if options.combine:
        logging.log("Combining files")
        output_path = f"{output_dir}.{output_format}"
        output.combine_audiofiles(filepaths, output_dir, output_path)
        filepaths = [output_path]
    # Add metadata
    if len(filepaths) == 1:
        add_metadata_to_file(audiobook, filepaths[0], options)
    else:
        add_metadata_to_dir(audiobook, filepaths, output_dir, options)


def add_metadata_to_file(audiobook: Audiobook, filepath: str, options):
    """Embed metadata into a single file"""
    if audiobook.chapters and not options.no_chapters:
        logging.log("Adding chapters")
        metadata.add_chapters(filepath, audiobook.chapters)
    logging.log("Adding metadata")
    metadata.add_metadata(filepath, audiobook.metadata)
    if audiobook.cover:
        logging.log("Embedding cover")
        metadata.embed_cover(filepath, audiobook.cover)


def add_metadata_to_dir(audiobook: Audiobook, filepaths: list[str], output_dir: str, options):
    """Add metadata to a directory with audio files"""
    for filepath in filepaths:
        metadata.add_metadata(filepath, audiobook.metadata)
    if audiobook.cover:
        logging.log("Adding cover")
        cover_path = os.path.join(output_dir, f"cover.{audiobook.cover.extension}")
        with open(cover_path, "wb") as f:
            f.write(audiobook.cover.image)


def download_files_with_cli_output(audiobook: Audiobook, output_dir: str) -> list[str]:
    """
    Download `audiobook` with cli output
    Returns a list of paths of the downloaded files
    """
    if len(audiobook.files) > 1:
        setup_download_dir(output_dir)
    with logging.progress(DOWNLOAD_PROGRESS) as progress:
        task = progress.add_task(
            f"Downloading {len(audiobook.files)} files [blue]{audiobook.title}",
            total = len(audiobook.files)
        )
        update_progress = partial(progress.advance, task)
        filepaths = download_files(audiobook, output_dir, update_progress)
        # Make sure progress bar is at 100%
        remaining_progress: float = progress.tasks[0].remaining or 0
        update_progress(remaining_progress)
        # Return filenames of downloaded files
        return filepaths


def create_filepath(audiobook: Audiobook, output_dir: str, index: int) -> str:
    """Create output file path for file number `index` in `audibook`"""
    extension = audiobook.files[index].ext
    if len(audiobook.files) == 1:
        path = f"{output_dir}.{extension}"
    else:
        name = f"{audiobook.title} - Part {index}.{extension}"
        path = os.path.join(output_dir, name)
    return path


def download_file(args: tuple[Audiobook, str, int, Any]) -> str:
    # Prepare download
    audiobook, output_dir, index, update_progress = args
    file = audiobook.files[index]
    filepath = create_filepath(audiobook, output_dir, index)
    logging.debug(f"Starting downloading file: {file.url}")
    request = audiobook.session.get(file.url, headers=file.headers, stream=True)
    total_filesize = int(request.headers["Content-length"])
    # Download file
    with open(filepath, "wb") as f:
        for chunk in request.iter_content(chunk_size=1024):
            f.write(chunk)
            download_progress = len(chunk)/total_filesize
            update_progress(download_progress)
    # Decrypt file if necessary
    if file.encryption_method:
        encryption.decrypt_file(filepath, file.encryption_method)
    # Return filepath
    return filepath


def download_files(audiobook: Audiobook, output_dir: str, update_progress) -> list[str]:
    """Download files from audiobook and return paths of the downloaded files"""
    filepaths = []
    with ThreadPool(processes=20) as pool:
        arguments = []
        for index in range(len(audiobook.files)):
            arguments.append((audiobook, output_dir, index, update_progress))
        for filepath in pool.imap(download_file, arguments):
            filepaths.append(filepath)
    return filepaths


def get_output_audio_format(option: Optional[str], files: list[str]) -> tuple[str, str]:
    """
    Get output format for files

    `option` is used if specied; else it's based on the file extensions
    """
    current_format = os.path.splitext(files[0])[1][1:]
    if option:
        output_format = option
    elif current_format == "ts":
        output_format = "mp3"
    else:
        output_format = current_format
    return current_format, output_format


def setup_download_dir(path: str):
    """Creates output folder"""
    if os.path.isdir(path):
        answer = Confirm.ask(f"The folder '[blue]{path}[/blue]' already exists. Do you want to override it?")
        if answer:
            shutil.rmtree(path)
        else:
            exit()
    os.makedirs(path)
