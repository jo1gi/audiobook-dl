import re
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

# List of file formats that use ID3 metadata
ID3_FORMATS = ["mp3", "mp4", "m4v", "m4a", "m4b"]

ID3_CONVERT = {
    "author": "artist",
    "series": "album",
}

def add_id3_metadata(filepath, metadata):
    """Add ID3 metadata tags to the given audio file"""
    audio = MP3(filepath, ID3=EasyID3)
    for key, value in metadata.items():
        if key in EasyID3.valid_keys.keys():
            audio[ID3_CONVERT[key]] = value
    audio.save(v2_version=3)

def add_metadata(filepath, metadata):
    """Adds metadata to the given audio file"""
    ext = re.search(r"(?<=(\.))\w+$", filepath).group(0)
    if ext in ID3_FORMATS:
        add_id3_metadata(filepath, metadata)

def embed_cover(filepath, image):
    """Emebds an image into the given audiofile"""
    audio = ID3(filepath)
    audio.add(APIC(type=3, data=image))
    audio.save()
