import os
import re
from datetime import date

from audiobookdl import logging, AudiobookMetadata, Cover
from mutagen.easymp4 import EasyMP4, EasyMP4Tags
from mutagen.mp4 import MP4, MP4Cover, Chapter as MP4Chapter, MP4Chapters

MP4_EXTENSIONS = ["mp4","m4a","m4p","m4b","m4r","m4v"]

MP4_CONVERT = {
    "authors": "artist",
    "narrators": "narrator",
    "publishers": "publisher",
    "series": "album",
    "title": "title",
    "genres": "genre",
}

MP4_COVER_FORMATS = {
    "jpg": MP4Cover.FORMAT_JPEG,
    "jpeg": MP4Cover.FORMAT_JPEG,
    "png": MP4Cover.FORMAT_PNG,
}

EasyMP4Tags.RegisterTextKey("year", 'yrrc')
EasyMP4Tags.RegisterTextKey("narrator", '\xa9nrt')
EasyMP4Tags.RegisterTextKey("publisher", '\xa9pub')
EasyMP4Tags.RegisterTextKey("track", '\xa9trk')
EasyMP4Tags.RegisterFreeformKey("scrape_url", "URL")

def is_mp4_file(filepath: str) -> bool:
    """Returns true if `filepath` points to an id3 file"""
    ext = re.search(r"(?<=(\.))\w+$", filepath)
    return ext is not None and ext.group(0) in MP4_EXTENSIONS


def add_mp4_metadata(filepath: str, metadata: AudiobookMetadata):
    """Add mp4 metadata tags to the given audio file"""
    audio = EasyMP4(filepath)
    for key, value in metadata.all_properties(allow_duplicate_keys=None):
        # System defined metadata tags
        if key == "release_date":
            release_date: date = value
            audio["date"] = release_date.strftime("%Y-%m-%d")
            audio["year"] = str(release_date.year)
        elif key == "language":
            audio.tags.RegisterFreeformKey(key, key.capitalize()) # type: ignore
            audio["language"] = value.alpha_3
        elif key == "series_order":
            audio["track"] = str(value)
        elif key in MP4_CONVERT:
            audio[MP4_CONVERT[key]] = value
        elif key in audio.Get.keys():
            audio[key] = value
        else:
            audio.tags.RegisterFreeformKey(key, key.capitalize()) # type: ignore
            audio[key] = value
    audio.save()
    # Mark `.m4b` files as audiobooks via Apple's "Media Kind" (`stik`) atom so
    # players enable audiobook behaviour (resume position, bookmarks, speed).
    if os.path.splitext(filepath)[1].lower() == ".m4b":
        mark_mp4_as_audiobook(filepath)


# Value of the MP4 `stik` (media kind) atom that marks a file as an audiobook
MP4_MEDIA_KIND_AUDIOBOOK = 2

def mark_mp4_as_audiobook(filepath: str):
    """Set the MP4 media-kind atom so the file is recognised as an audiobook"""
    audio = MP4(filepath)
    audio["stik"] = [MP4_MEDIA_KIND_AUDIOBOOK]
    audio.save()


def embed_mp4_cover(filepath: str, cover: Cover):
    if not cover.extension in MP4_COVER_FORMATS:
        return
    audio = MP4(filepath)
    audio["covr"] = [
        MP4Cover(cover.image, imageformat=MP4_COVER_FORMATS[cover.extension])
    ]
    audio.save()
