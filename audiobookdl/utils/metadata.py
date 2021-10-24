import re
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, CHAP, TIT2, CTOC, CTOCFlags
from typing import Dict

# List of file formats that use ID3 metadata
ID3_FORMATS = ["mp3", "mp4", "m4v", "m4a", "m4b"]

ID3_CONVERT = {
    "author": "artist",
    "series": "album",
    "title": "title",
}

EXTENSION_TO_MIMETYPE = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
}


def add_id3_metadata(filepath: str, metadata: Dict[str, str]):
    """Add ID3 metadata tags to the given audio file"""
    audio = MP3(filepath, ID3=EasyID3)
    for key, value in metadata.items():
        if key in EasyID3.valid_keys.keys():
            audio[ID3_CONVERT[key]] = value
    audio.save(v2_version=3)


def add_metadata(filepath: str, metadata: Dict[str, str]):
    """Adds metadata to the given audio file"""
    ext = re.search(r"(?<=(\.))\w+$", filepath)
    if ext is None:
        return
    if ext.group(0) in ID3_FORMATS:
        add_id3_metadata(filepath, metadata)


def embed_cover(filepath: str, image: bytes, extension: str):
    """Embeds an image into the given audio file"""
    mimetype = EXTENSION_TO_MIMETYPE[extension]
    audio = ID3(filepath)
    audio.add(APIC(type=0, data=image, mime=mimetype))
    audio.save()


def add_chapter(audio: ID3, start: int, end: int, title: str, index: int):
    """Adds a single chapter to the given audio file"""
    audio.add(CHAP(
        element_id=u"chp"+str(index),
        start_time=int(start),
        end_time=int(end),
        sub_frames=[TIT2(text=[title])]))


def add_chapters(filepath, chapters):
    """Adds chapters to the given audio file"""
    audio = ID3(filepath)
    # Adding table of contents
    audio.add(CTOC(
        element_id=u"toc",
        flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
        child_element_ids=[u"chp"+str(i+1) for i in range(len(chapters))],
        sub_frames=[TIT2(text=[u"Table of Contents"])]))
    # Adding chapters
    for i in range(len(chapters)-1):
        add_chapter(
                audio,
                chapters[i][0],
                chapters[i+1][0],
                chapters[i][1], i+1)
    length = MutagenFile(filepath).info.length*1000
    add_chapter(audio, chapters[-1][0], length, chapters[-1][1], len(chapters))
    audio.save()
