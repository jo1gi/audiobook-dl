import re
import os
from datetime import date
from audiobookdl import logging, Chapter, AudiobookMetadata, Cover

from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3, EasyID3KeyError
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, CHAP, TIT2, TIT1, CTOC, CTOCFlags, WCOM, ID3NoHeaderError
from requests import utils
from rich.progress import Progress, SpinnerColumn, TextColumn

from typing import Sequence

EasyID3.RegisterTextKey("comment", "COMM")
EasyID3.RegisterTextKey("year", "TYER")
EasyID3.RegisterTextKey("originalreleaseyear", "TORY")
EasyID3.RegisterTXXXKey("isbn", "ISBN")
# Audiobook-specific TXXX tags for better app compatibility
EasyID3.RegisterTXXXKey("series_txxx", "SERIES")
EasyID3.RegisterTXXXKey("series_part", "SERIES-PART")
EasyID3.RegisterTXXXKey("asin", "ASIN")
EasyID3.RegisterTXXXKey("subtitle", "Subtitle")

def commercialurl_get(id3, key):
    urls = [frame.url for frame in id3.getall("WCOM")]
    if urls:
        return urls
    else:
        raise EasyID3KeyError(key)

def commercialurl_set(id3, key, value):
    id3.delall("WCOM")
    for v in value:
        # scrape urls might contain characters in the unicode range
        # for audiobooks with non-english titles
        encoded_url = utils.requote_uri(v)
        id3.add(WCOM(url=encoded_url))

def commercialurl_delete(id3, key):
    id3.delall("WCOM")

EasyID3.RegisterKey("commercialurl", commercialurl_get, commercialurl_set, commercialurl_delete)

# Conversion table between metadata names and ID3 tags
ID3_CONVERT = {
    "authors": "artist",
    "authors_album": "albumartist",  # TPE2 - for Plex compatibility
    "series": "album",
    "title": "title",
    "publisher": "organization", # TPUB
    "description": "comment", # COMM
    "genres": "genre", # TCON
    "scrape_url": "commercialurl", # WCOM
}

# List of file formats that use ID3 metadata
ID3_FORMATS = ["mp3"]

EXTENSION_TO_MIMETYPE = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
}

def is_id3_file(filepath: str) -> bool:
    """Returns true if `filepath` points to an id3 file"""
    ext = re.search(r"(?<=(\.))\w+$", filepath)
    return ext is not None and ext.group(0) in ID3_FORMATS


def add_id3_metadata(filepath: str, metadata: AudiobookMetadata):
    """Add ID3 metadata tags to the given audio file"""
    filename = os.path.basename(filepath)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(f"Adding metadata to {filename}", total=None)

        audio = MP3(filepath, ID3=EasyID3)
        # Store series info for Content Group formatting
        series_name = None
        series_order = None

        # Adding tags
        for key, value in metadata.all_properties(allow_duplicate_keys=None):
            if key == "release_date":
                audio["originaldate"] = value.strftime("%Y-%m-%d")
                audio["year"] = str(value.year)
            elif key == "language":
                # Convert ISO 639-3 code to full language name (e.g., "English", "Swedish")
                audio["language"] = value.name if hasattr(value, 'name') else str(value)
            elif key == "narrators":
                audio["composer"] = value
                audio["performer"] = value
            elif key == "authors":
                # Write authors to both artist and albumartist for compatibility
                audio["artist"] = value
                audio["albumartist"] = value
            elif key == "genres":
                # Join multiple genres with " / " for proper display in audiobook apps
                genres_str = " / ".join(value) if isinstance(value, list) else value
                audio["genre"] = genres_str
            elif key == "series":
                # Store for Content Group and write to album tag
                series_name = value
                audio["album"] = value
                # Also write to TXXX:SERIES for Plex/audiobookshelf
                audio["series_txxx"] = value
            elif key == "series_order":
                # Store for Content Group
                series_order = value
                audio["tracknumber"] = str(value)
                # Also write to TXXX:SERIES-PART for Plex/audiobookshelf
                audio["series_part"] = str(value)
            elif key == "isbn":
                audio["isbn"] = value
            elif key in ID3_CONVERT:
                audio[ID3_CONVERT[key]] = value
            elif key in EasyID3.valid_keys.keys():
                audio[key] = value

        # Save with EasyID3 first
        audio.save(v2_version=4)

        # Now use raw ID3 to add Content Group (TIT1) for Plex
        # Format: "Series, Book #"
        if series_name and series_order is not None:
            raw_audio = ID3(filepath)
            content_group = f"{series_name}, Book {series_order}"
            raw_audio.add(TIT1(text=[content_group]))
            raw_audio.save(v2_version=4)


def embed_id3_cover(filepath: str, cover: Cover):
    filename = os.path.basename(filepath)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(f"Embedding cover art to {filename}", total=None)

        mimetype = EXTENSION_TO_MIMETYPE[cover.extension]
        try:
            audio = ID3(filepath)
        except ID3NoHeaderError:
            return
        audio.add(APIC(type=0, data=cover.image, mime=mimetype))
        audio.save()


def add_id3_chapter(audio: ID3, start: int, end: int, title: str, index: int):
    """Adds a single chapter to the given audio file"""
    audio.add(CHAP(
        element_id=u"chp"+str(index),
        start_time=int(start),
        end_time=int(end),
        sub_frames=[TIT2(text=[title])]
    ))


def add_id3_chapters(filepath: str, chapters: Sequence[Chapter]):
    """Adds chapters to the given audio file"""
    filename = os.path.basename(filepath)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(f"Adding {len(chapters)} chapters to {filename}", total=None)

        audio = ID3(filepath)
        for i in range(len(chapters)-1):
            add_id3_chapter(
                audio,
                start = chapters[i].start,
                end = chapters[i+1].start,
                title = chapters[i].title,
                index = i+1
            )
        length = MutagenFile(filepath).info.length*1000
        add_id3_chapter(audio, chapters[-1].start, length, chapters[-1].title, len(chapters))
        audio.save()
