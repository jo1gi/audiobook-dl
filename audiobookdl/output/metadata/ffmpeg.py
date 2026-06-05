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
    if MutagenFile(filepath) is None:
        logging.debug(f"Skipping chapters: {filepath} is a container without chapter support (e.g. raw AAC)")
        return
    try:
        with open(TMP_CHAPTER_FILE, "w") as f:
            f.write(create_tmp_chapter_file(filepath, chapters))
        result = subprocess.run(
            ["ffmpeg", "-y",
             "-i", filepath,
             "-i", TMP_CHAPTER_FILE,
             "-map_chapters", "1",
             "-c", "copy",
             "-map", "0:a",
             "-metadata:s:a:0", "title=",
             TMP_MEDIA_FILE],
            capture_output = not logging.ffmpeg_output
        )
        produced_output = (
            os.path.exists(TMP_MEDIA_FILE) and os.path.getsize(TMP_MEDIA_FILE) > 0
        )
        if result.returncode != 0 or not produced_output:
            logging.debug("add_chapters_ffmpeg copy mode failed, retrying with re-encode")
            if os.path.exists(TMP_MEDIA_FILE):
                os.remove(TMP_MEDIA_FILE)
            subprocess.run(
                ["ffmpeg", "-y",
                 "-i", filepath,
                 "-i", TMP_CHAPTER_FILE,
                 "-map_chapters", "1",
                 "-c:a", "aac",
                 "-b:a", "128k",
                 "-map", "0:a",
                 "-metadata:s:a:0", "title=",
                 TMP_MEDIA_FILE],
                capture_output = not logging.ffmpeg_output
            )
        # ffmpeg produced no output: keep the chapterless original instead of crashing the run
        if not (os.path.exists(TMP_MEDIA_FILE) and os.path.getsize(TMP_MEDIA_FILE) > 0):
            logging.log("Could not embed chapters; leaving file as-is")
            return
        os.remove(filepath)
        os.rename(TMP_MEDIA_FILE, filepath)
    finally:
        if os.path.exists(TMP_CHAPTER_FILE):
            os.remove(TMP_CHAPTER_FILE)
        if os.path.exists(TMP_MEDIA_FILE):
            os.remove(TMP_MEDIA_FILE)
        
