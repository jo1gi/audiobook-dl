from audiobookdl import Chapter, utils, logging
from mutagen import File as MutagenFile
import subprocess
import os
import tempfile
from typing import Sequence

def create_chapter_text(title: str, start: int, end: int) -> str:
    chapter_template = utils.read_asset_file("assets/ffmpeg_chapter_template.txt")
    return chapter_template.format(
        title = title,
        start = start,
        end = end
    )


def _normalize_chapters(chapters: Sequence[Chapter]) -> Sequence[Chapter]:
    normalized = []
    seen = set()
    for chapter in sorted(chapters, key=lambda c: int(c.start)):
        start = int(chapter.start)
        if start in seen:
            continue
        seen.add(start)
        normalized.append(Chapter(start=start, title=chapter.title))
    return normalized


def create_tmp_chapter_file(filepath: str, chapters: Sequence[Chapter]) -> str:
    result = ";FFMETADATA1\n"
    chapters = _normalize_chapters(chapters)
    if not chapters:
        return result
    for i in range(len(chapters)-1):
        chapter = chapters[i]
        next_start = chapters[i+1].start
        if next_start <= chapter.start:
            continue
        result += create_chapter_text(chapter.title, chapter.start, next_start)
    length = MutagenFile(filepath).info.length*1000
    last_chapter = chapters[-1]
    end = max(last_chapter.start + 1, int(length))
    result += create_chapter_text(
        title = last_chapter.title,
        start = last_chapter.start,
        end = end
    )
    return result

def add_chapters_ffmpeg(filepath: str, chapters: Sequence[Chapter]):
    tmp_chapter_file = None
    tmp_media_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".ffmeta",
            delete=False
        ) as f:
            tmp_chapter_file = f.name
            f.write(create_tmp_chapter_file(filepath, chapters))

        _, output_ext = os.path.splitext(filepath)
        with tempfile.NamedTemporaryFile(
            suffix=output_ext or ".tmp",
            delete=False
        ) as f:
            tmp_media_file = f.name

        subprocess.run(
            ["ffmpeg", "-y", 
             "-i", filepath, 
             "-f", "ffmetadata",
             "-i", tmp_chapter_file,
             "-map_chapters", "1",
             "-c", "copy",
             "-map", "0",
              "-metadata:s:a:0", "title=",
             tmp_media_file],
            capture_output = not logging.ffmpeg_output,
            check=True
        )
        os.replace(tmp_media_file, filepath)
    finally:
        if tmp_chapter_file and os.path.exists(tmp_chapter_file):
            os.remove(tmp_chapter_file)
        if tmp_media_file and os.path.exists(tmp_media_file):
            os.remove(tmp_media_file)
        
