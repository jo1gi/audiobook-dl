from audiobookdl import logging, AudiobookMetadata
from audiobookdl.exceptions import FailedCombining

import os
import shutil
import platform
import subprocess
from multiprocessing.pool import ThreadPool
from typing import Sequence, Mapping

LOCATION_DEFAULTS = {
    'album': 'NA',
    'artist': 'NA',
}

# Number of parallel ffmpeg remux processes when preparing files for combining
COMBINE_REMUX_THREADS = 16
# Containers that need the ADTS-to-ASC bitstream filter for raw AAC streams
MP4_CONTAINERS = ("mp4", "m4a", "m4b", "mov")

def gen_output_filename(booktitle: str, file: Mapping[str, str], template: str) -> str:
    """Generates an output filename based on different attributes of the
    file"""
    arguments = {**file, **{"booktitle": booktitle}}
    filename = template.format(**arguments)
    return _fix_output(filename)


def _ffmpeg_audio_codec(path: str) -> str:
    """Returns the codec name of the first audio stream in `path` (empty on failure)"""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def _ffprobe_duration(path: str) -> float:
    """Returns the duration of `path` in seconds (0.0 on failure)"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _remux_to_mpegts(source: str, ts_path: str) -> bool:
    """
    Remux a single audio file into an MPEG-TS container.

    Concatenating raw segments directly (e.g. ADTS-AAC) desyncs the decoder at
    segment boundaries and silently drops most of the audio. Remuxing each
    segment to MPEG-TS first gives every part clean framing and timestamps, so
    the following concatenation is lossless.

    :returns: `True` if a non-empty file was produced
    """
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", source, "-c", "copy", "-f", "mpegts", ts_path],
        capture_output=not logging.ffmpeg_output,
    )
    if os.path.exists(ts_path) and os.path.getsize(ts_path) > 0:
        return True
    if result.stderr:
        logging.debug(result.stderr.decode("utf8", "replace"))
    return False


def combine_audiofiles(filepaths: Sequence[str], tmp_dir: str, output_path: str):
    """
    Combines the given audiofiles in `path` into a new file

    :param filepaths: Paths to audio files
    :param tmp_dir: Temporary directory with audio files
    :param output_path: Path of combined audio files
    """
    output_extension = get_extension(output_path)
    ts_dir = os.path.join(tmp_dir, "ts_parts")
    os.makedirs(ts_dir, exist_ok=True)
    # Remux every segment to MPEG-TS in parallel (lossless copy)
    padding = len(str(len(filepaths)))
    def remux(item):
        index, source = item
        ts_path = os.path.join(ts_dir, f"{str(index).zfill(padding)}.ts")
        return ts_path, _remux_to_mpegts(source, ts_path)
    with ThreadPool(processes=COMBINE_REMUX_THREADS) as pool:
        remuxed = pool.map(remux, list(enumerate(filepaths)))
    ts_paths = []
    for ts_path, ok in remuxed:
        if not ok:
            raise FailedCombining
        ts_paths.append(ts_path)
    # Binary-concatenate the MPEG-TS parts. The ffmpeg concat *demuxer* aborts
    # early on some segment junctions (returning success while silently dropping
    # most of the audio); MPEG-TS is designed for splicing, so a raw byte
    # concatenation of the remuxed parts is both robust and lossless.
    combined_ts = os.path.join(tmp_dir, "combined.ts")
    with open(combined_ts, "wb") as out:
        for ts_path in ts_paths:
            with open(ts_path, "rb") as part:
                shutil.copyfileobj(part, out)
    # Remux the concatenated stream into the requested output container
    command = ["ffmpeg", "-y", "-i", combined_ts, "-c", "copy"]
    # AAC streams need the ADTS-to-ASC bitstream filter when written into MP4-family files
    if output_extension in MP4_CONTAINERS and _ffmpeg_audio_codec(ts_paths[0]) == "aac":
        command += ["-bsf:a", "aac_adtstoasc"]
    command.append(output_path)
    result = subprocess.run(command, capture_output=not logging.ffmpeg_output)
    if not (os.path.exists(output_path) and os.path.getsize(output_path) > 0):
        if result.stderr:
            logging.debug(result.stderr.decode("utf8", "replace"))
        raise FailedCombining
    # Guard against silent truncation: the combined file must be about as long
    # as the concatenated source. A large shortfall means ffmpeg dropped audio.
    expected = _ffprobe_duration(combined_ts)
    actual = _ffprobe_duration(output_path)
    if expected > 0 and actual < expected * 0.98:
        logging.debug(
            f"Combined output is shorter than expected "
            f"({actual:.0f}s vs {expected:.0f}s); combine truncated the audio"
        )
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
