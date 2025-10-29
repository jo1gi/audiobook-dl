from audiobookdl import logging, AudiobookMetadata
from audiobookdl.exceptions import FailedCombining, MissingEncoder
from .ffmpeg_progress import (
    run_ffmpeg_with_progress,
    get_media_duration,
    create_progress_task
)

import os
import shutil
import platform
import subprocess
from typing import Sequence, Mapping, List, Union
from rich.progress import BarColumn, ProgressColumn, SpinnerColumn

# Progress bar format for ffmpeg operations
FFMPEG_PROGRESS: List[Union[str, ProgressColumn]] = [
    SpinnerColumn(),
    "{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%"
]

LOCATION_DEFAULTS = {
    'album': 'NA',
    'artist': 'NA',
}

COMBINE_CHUNK_SIZE = 500

def gen_output_filename(booktitle: str, file: Mapping[str, str], template: str) -> str:
    """Generates an output filename based on different attributes of the
    file"""
    arguments = {**file, **{"booktitle": booktitle}}
    filename = template.format(**arguments)
    return _fix_output(filename)


def combine_audiofiles(filepaths: Sequence[str], tmp_dir: str, output_path: str):
    """
    Combines the given audiofiles in `path` into a new file

    :param filepaths: Paths to audio files
    :param tmp_dir: Temporary directory with audio files
    :param output_path: Path of combined audio files
    """
    output_extension = get_extension(output_path)
    tmp_input = os.path.join(tmp_dir, f"input_file.{output_extension}")
    tmp_output = os.path.join(tmp_dir, f"output_file.{output_extension}")
    shutil.move(filepaths[0], tmp_input)

    # Calculate total chunks for progress tracking
    num_chunks = (len(filepaths) - 1 + COMBINE_CHUNK_SIZE - 1) // COMBINE_CHUNK_SIZE

    # In debug mode, skip progress bar and show ffmpeg output directly
    if logging.ffmpeg_output:
        for chunk_idx, i in enumerate(range(1, len(filepaths), COMBINE_CHUNK_SIZE)):
            chunk_files = filepaths[i:i+COMBINE_CHUNK_SIZE]

            # Use concat demuxer with file list to avoid "too many open files" error
            concat_list_path = os.path.join(tmp_dir, "concat_list.txt")
            with open(concat_list_path, "w") as f:
                f.write(f"file '{tmp_input}'\n")
                for filepath in chunk_files:
                    # Escape single quotes in filepath
                    escaped_path = filepath.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            command = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy",
                tmp_output
            ]

            # Run ffmpeg directly in debug mode
            result = subprocess.run(command)
            if result.returncode != 0:
                logging.log(f"[red]Error combining files[/red]")
                raise subprocess.CalledProcessError(result.returncode, command)

            os.remove(tmp_input)
            os.remove(concat_list_path)
            shutil.move(tmp_output, tmp_input)
    else:
        # Create progress bar for combining in normal mode
        with logging.progress(FFMPEG_PROGRESS) as progress:
            for chunk_idx, i in enumerate(range(1, len(filepaths), COMBINE_CHUNK_SIZE)):
                chunk_files = filepaths[i:i+COMBINE_CHUNK_SIZE]

                # Get duration for progress tracking
                duration = get_media_duration(tmp_input)
                description = f"Combining files (chunk {chunk_idx + 1}/{num_chunks})"
                task = create_progress_task(progress, description, duration)

                # Use concat demuxer with file list to avoid "too many open files" error
                concat_list_path = os.path.join(tmp_dir, "concat_list.txt")
                with open(concat_list_path, "w") as f:
                    f.write(f"file '{tmp_input}'\n")
                    for filepath in chunk_files:
                        # Escape single quotes in filepath
                        escaped_path = filepath.replace("'", "'\\''")
                        f.write(f"file '{escaped_path}'\n")

                command = [
                    "ffmpeg",
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list_path,
                    "-c", "copy",
                    tmp_output
                ]

                # Run with progress tracking
                returncode, stdout, stderr = run_ffmpeg_with_progress(
                    command, progress, task, duration, description
                )

                # Check for errors
                if returncode != 0:
                    logging.log(f"[red]Error combining files:[/red] {stderr}")
                    raise subprocess.CalledProcessError(returncode, command, stdout, stderr)

                os.remove(tmp_input)
                os.remove(concat_list_path)
                shutil.move(tmp_output, tmp_input)

    shutil.move(tmp_input, output_path)
    if not os.path.exists(output_path):
        raise FailedCombining
    shutil.rmtree(tmp_dir)


def get_extension(path: str) -> str:
    """
    Get extension from path

    :param path: Path to get extension from
    :returns: Extension of path
    """
    return os.path.splitext(path)[1][1:]


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


def check_encoder_available(encoder: str) -> bool:
    """
    Check if a specific encoder is available in ffmpeg

    :param encoder: Name of the encoder to check
    :returns: True if the encoder is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Check if the encoder name appears in the output
        # Encoder lines typically look like: " A..... aac                  AAC (Advanced Audio Coding)"
        return encoder in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_audio_bitrate(filepath: str) -> Union[int, None]:
    """
    Get the audio bitrate of a file using ffprobe

    :param filepath: Path to the audio file
    :returns: Bitrate in kbit/s (e.g., 64 for 64k), or None if detection fails
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-select_streams", "a:0", filepath],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if "streams" in data and len(data["streams"]) > 0:
                stream = data["streams"][0]
                # Try to get bitrate from stream info
                if "bit_rate" in stream:
                    # Convert from bits/s to kbits/s
                    bitrate_kbps = int(stream["bit_rate"]) // 1000
                    return bitrate_kbps
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
        return None


def convert_output(filenames: Sequence[str], output_format: str, mp4_audio_encoder: str = None):
    """Converts a list of audio files into another format and return new
    files

    :param filenames: List of input files to convert
    :param output_format: Target output format
    :param mp4_audio_encoder: Audio encoder for MP4/M4A/M4B files (default: aac)
    """
    new_paths = []

    # In debug mode, skip progress bar and show ffmpeg output directly
    if logging.ffmpeg_output:
        for old_path in filenames:
            path_without_ext, old_ext = os.path.splitext(old_path)
            new_path = f"{path_without_ext}.{output_format}"
            if not output_format == old_ext:
                # Build ffmpeg command
                if can_copy_codec(old_ext, output_format):
                    command = ["ffmpeg", "-y", "-i", old_path, "-codec", "copy", new_path]
                else:
                    # Check if output format is MP4-based and needs encoder specification
                    mp4_formats = ["mp4", "m4a", "m4b", "m4r", "m4v", "m4p"]
                    if output_format in mp4_formats:
                        encoder = mp4_audio_encoder or "aac"
                        # Verify encoder is available
                        if not check_encoder_available(encoder):
                            raise MissingEncoder(
                                error_description=f"FFmpeg encoder '{encoder}' not found. "
                                f"Install ffmpeg with support for '{encoder}' or use a different encoder "
                                f"(e.g., aac, aac_at, libfdk_aac)"
                            )
                        # Detect source bitrate and match it
                        bitrate = get_audio_bitrate(old_path)
                        if bitrate:
                            command = ["ffmpeg", "-y", "-i", old_path, "-c:a", encoder, "-b:a", f"{bitrate}k", new_path]
                        else:
                            command = ["ffmpeg", "-y", "-i", old_path, "-c:a", encoder, new_path]
                    else:
                        command = ["ffmpeg", "-y", "-i", old_path, new_path]

                # Run ffmpeg directly in debug mode
                result = subprocess.run(command)
                if result.returncode != 0:
                    filename = os.path.basename(old_path)
                    logging.log(f"[red]Error converting {filename}[/red]")
                    raise subprocess.CalledProcessError(result.returncode, command)

                os.remove(old_path)
            new_paths.append(new_path)
    else:
        # Create progress bar for conversion in normal mode
        with logging.progress(FFMPEG_PROGRESS) as progress:
            for old_path in filenames:
                path_without_ext, old_ext = os.path.splitext(old_path)
                new_path = f"{path_without_ext}.{output_format}"
                if not output_format == old_ext:
                    # Get duration for progress tracking
                    duration = get_media_duration(old_path)
                    filename = os.path.basename(old_path)
                    description = f"Converting {filename}"

                    # Create progress task
                    task = create_progress_task(progress, description, duration)

                    # Build ffmpeg command
                    if can_copy_codec(old_ext, output_format):
                        command = ["ffmpeg", "-y", "-i", old_path, "-codec", "copy", new_path]
                    else:
                        # Check if output format is MP4-based and needs encoder specification
                        mp4_formats = ["mp4", "m4a", "m4b", "m4r", "m4v", "m4p"]
                        if output_format in mp4_formats:
                            encoder = mp4_audio_encoder or "aac"
                            # Verify encoder is available
                            if not check_encoder_available(encoder):
                                raise MissingEncoder(
                                    error_description=f"FFmpeg encoder '{encoder}' not found. "
                                    f"Install ffmpeg with support for '{encoder}' or use a different encoder "
                                    f"(e.g., aac, aac_at, libfdk_aac)"
                                )
                            # Detect source bitrate and match it
                            bitrate = get_audio_bitrate(old_path)
                            if bitrate:
                                command = ["ffmpeg", "-y", "-i", old_path, "-c:a", encoder, "-b:a", f"{bitrate}k", new_path]
                            else:
                                command = ["ffmpeg", "-y", "-i", old_path, "-c:a", encoder, new_path]
                        else:
                            command = ["ffmpeg", "-y", "-i", old_path, new_path]

                    # Run with progress tracking
                    returncode, stdout, stderr = run_ffmpeg_with_progress(
                        command, progress, task, duration, description
                    )

                    # Check for errors
                    if returncode != 0:
                        logging.log(f"[red]Error converting {filename}:[/red] {stderr}")
                        raise subprocess.CalledProcessError(returncode, command, stdout, stderr)

                    os.remove(old_path)
                new_paths.append(new_path)

    return new_paths

def get_max_name_length() -> int:
    """
    Get the max length for file names supported by the OS

    :returns: max length for file names
    """
    try:
        # should work on Linux/MacOS
        return os.pathconf(".", "PC_NAME_MAX")
    except:
        try:
            # Windows
            from ctypes.wintypes import MAX_PATH
            return MAX_PATH
        except:
            # default
            return 255

def gen_output_location(template: str, metadata: AudiobookMetadata, remove_chars: str) -> str:
    """
    Generates the location of the output based on attributes of the audiobook.

    :param template: Python string template audiobook metadata is put into
    :param metadata: Audiobook metadata,
    :param remove_chars: List of characters to be removed from the final path
    :returns: `template` with metadata inserted
    """
    max_name_length = get_max_name_length()

    # Expand ~ to home directory before formatting
    template = os.path.expanduser(template)

    if metadata is None:
        metadata = {}
    title = _fix_output(metadata.title)
    title_bytes = title.encode('utf-8')
    title_len = len(title_bytes)
    ext_len = 9 # extra length needed for file extensions: len('.mp3.json')
    if title_len > max_name_length - ext_len:
        title = title_bytes[0:max_name_length-ext_len].decode('utf-8', errors='ignore')
        logging.log(f"title to long, using [blue]{title}[/blue] as filename base")
    metadata_dict = {**LOCATION_DEFAULTS, **metadata.all_properties_dict()}
    metadata_dict['title'] = title
    # If author is missing but narrator exists, use narrator as author
    if (not metadata_dict.get('author') or metadata_dict.get('author') == '') and metadata_dict.get('narrator'):
        metadata_dict['author'] = metadata_dict['narrator']
    # Apply remove_chars to each metadata value, not to the path structure
    for key, value in metadata_dict.items():
        if isinstance(value, str):
            metadata_dict[key] = _remove_chars(value, remove_chars)
    formatted = template.format(**metadata_dict)
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
