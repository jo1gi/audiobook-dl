import re
import os
from datetime import date

from audiobookdl import logging, AudiobookMetadata, Cover
from mutagen.easymp4 import EasyMP4, EasyMP4Tags
from mutagen.mp4 import MP4, MP4Cover, Chapter as MP4Chapter, MP4Chapters
from rich.progress import Progress, SpinnerColumn, TextColumn

MP4_EXTENSIONS = ["mp4","m4a","m4p","m4b","m4r","m4v"]

MP4_CONVERT = {
    "title": "album",
    "authors": "artist",
    "narrators": "composer",
    "genres": "genre",
    "publisher": "publisher",
}

MP4_COVER_FORMATS = {
    "jpg": MP4Cover.FORMAT_JPEG,
    "jpeg": MP4Cover.FORMAT_JPEG,
    "png": MP4Cover.FORMAT_PNG,
}

EasyMP4Tags.RegisterTextKey("year", 'yrrc')
EasyMP4Tags.RegisterTextKey("narrator", '\xa9nrt')
EasyMP4Tags.RegisterTextKey("composer", '\xa9wrt')
EasyMP4Tags.RegisterTextKey("publisher", '\xa9pub')
EasyMP4Tags.RegisterTextKey("track", '\xa9trk')
EasyMP4Tags.RegisterFreeformKey("scrape_url", "URL")

def is_mp4_file(filepath: str) -> bool:
    """Returns true if `filepath` points to an id3 file"""
    ext = re.search(r"(?<=(\.))\w+$", filepath)
    return ext is not None and ext.group(0) in MP4_EXTENSIONS


def add_mp4_metadata(filepath: str, metadata: AudiobookMetadata):
    """Add mp4 metadata tags to the given audio file"""
    filename = os.path.basename(filepath)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(f"Adding metadata to {filename}", total=None)

        audio = EasyMP4(filepath)
        for key, value in metadata.all_properties(allow_duplicate_keys=None):
            # System defined metadata tags
            if key == "release_date":
                release_date: date = value
                audio["date"] = release_date.strftime("%Y-%m-%d")
                audio["year"] = str(release_date.year)
            elif key == "language":
                # Convert ISO 639-3 code to full language name
                audio.tags.RegisterFreeformKey(key, key.capitalize()) # type: ignore
                audio["language"] = value.name if hasattr(value, 'name') else str(value)
            elif key == "series":
                # Use custom rDNSatom for series
                audio.tags.RegisterFreeformKey(key, key) # type: ignore
                audio[key] = value
            elif key == "series_order":
                # Use custom rDNSatom with name "mvin"
                audio.tags.RegisterFreeformKey("mvin", "mvin") # type: ignore
                audio["mvin"] = str(value)
            elif key == "authors":
                # Join multiple authors with ", "
                authors_str = ", ".join(value) if isinstance(value, list) else value
                audio[MP4_CONVERT[key]] = authors_str
            elif key == "narrators":
                # Join multiple narrators with ", "
                narrators_str = ", ".join(value) if isinstance(value, list) else value
                audio[MP4_CONVERT[key]] = narrators_str
            elif key == "genres":
                # Join multiple genres with " / "
                genres_str = " / ".join(value) if isinstance(value, list) else value
                audio[MP4_CONVERT[key]] = genres_str
            elif key == "isbn":
                # Store ISBN as lowercase "isbn"
                audio.tags.RegisterFreeformKey("isbn", "isbn") # type: ignore
                audio["isbn"] = value
            elif key == "publisher":
                # Store publisher in both standard and lowercase freeform
                audio[MP4_CONVERT[key]] = value
                audio.tags.RegisterFreeformKey("publisher", "publisher") # type: ignore
                audio["publisher"] = value
            elif key in MP4_CONVERT:
                audio[MP4_CONVERT[key]] = value
            elif key in audio.Get.keys():
                audio[key] = value
            else:
                audio.tags.RegisterFreeformKey(key, key.capitalize()) # type: ignore
                audio[key] = value
        audio.save()


def embed_mp4_cover(filepath: str, cover: Cover):
    if not cover.extension in MP4_COVER_FORMATS:
        return

    filename = os.path.basename(filepath)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(f"Embedding cover art to {filename}", total=None)

        audio = MP4(filepath)
        audio["covr"] = [
            MP4Cover(cover.image, imageformat=MP4_COVER_FORMATS[cover.extension])
        ]
        audio.save()
