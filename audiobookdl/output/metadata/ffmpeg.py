from audiobookdl import Chapter, utils, logging
from mutagen import File as MutagenFile
import subprocess
import os
from typing import Sequence

TMP_CHAPTER_FILE = "chapters.tmp.txt"
TMP_MEDIA_FILE = "audiobook.tmp.mp4"

def create_chapter_text(title: str, start: int, end: int) -> str:
    chapter_template = utils.read_asset_file("assets/ffmpeg_chapter_template.txt")
    return chapter_template.format(
        title = title,
        start = start,
        end = end
    )


def create_tmp_chapter_file(filepath: str, chapters: Sequence[Chapter]) -> str:
    result = ";FFMETADATA1\n"
    for i in range(len(chapters)-1):
        chapter = chapters[i]
        result += create_chapter_text(chapter.title, chapter.start, chapters[i+1].start)
    length = MutagenFile(filepath).info.length*1000
    last_chapter = chapters[-1]
    result += create_chapter_text(
        title = last_chapter.title,
        start = last_chapter.start,
        end = int(length)
    )
    return result

def add_chapters_ffmpeg(filepath: str, chapters: Sequence[Chapter]):
    try:
        with open(TMP_CHAPTER_FILE, "w") as f:
            f.write(create_tmp_chapter_file(filepath, chapters))
        subprocess.run(
            ["ffmpeg", "-y", "-i", filepath, "-i", TMP_CHAPTER_FILE,
                "-map_metadata", "1", "-c", "copy", TMP_MEDIA_FILE],
            capture_output = not logging.ffmpeg_output
        )
        os.remove(filepath)
        os.rename(TMP_MEDIA_FILE, filepath)
    finally:
        os.remove(TMP_CHAPTER_FILE)
