from audiobookdl import Chapter, utils, logging
from mutagen import File as MutagenFile
from ..ffmpeg_progress import (
    run_ffmpeg_with_progress,
    get_media_duration,
    create_progress_task
)
import subprocess
import os
from typing import Sequence, List, Union
from rich.progress import BarColumn, ProgressColumn, SpinnerColumn

# Progress bar format for ffmpeg operations
FFMPEG_PROGRESS: List[Union[str, ProgressColumn]] = [
    SpinnerColumn(),
    "{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%"
]

# Temp file names (will be created in the same directory as the output file)
TMP_CHAPTER_FILENAME = "chapters.tmp.txt"
TMP_MEDIA_FILENAME = "audiobook.tmp.mp4"

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
    # Create temp files in the same directory as the output file
    output_dir = os.path.dirname(filepath) or "."
    tmp_chapter_file = os.path.join(output_dir, TMP_CHAPTER_FILENAME)
    tmp_media_file = os.path.join(output_dir, TMP_MEDIA_FILENAME)

    try:
        with open(tmp_chapter_file, "w") as f:
            f.write(create_tmp_chapter_file(filepath, chapters))

        command = [
            "ffmpeg", "-y",
            "-i", filepath,
            "-i", tmp_chapter_file,
            "-map_chapters", "1",
            "-c", "copy",
            "-map", "0",
            "-metadata:s:a:0", "title=",
            tmp_media_file
        ]

        # In debug mode, skip progress bar and show ffmpeg output directly
        if logging.ffmpeg_output:
            result = subprocess.run(command)
            returncode = result.returncode
        else:
            # Run with progress tracking in normal mode
            duration = get_media_duration(filepath)
            filename = os.path.basename(filepath)
            description = f"Adding chapters to {filename}"

            with logging.progress(FFMPEG_PROGRESS) as progress:
                task = create_progress_task(progress, description, duration)
                returncode, stdout, stderr = run_ffmpeg_with_progress(
                    command, progress, task, duration, description
                )

        # Check if ffmpeg succeeded and created the temp file
        if returncode != 0 or not os.path.exists(tmp_media_file):
            logging.log(f"[yellow]Warning: Failed to add chapters using ffmpeg (return code: {returncode})[/yellow]")
            return

        os.remove(filepath)
        os.rename(tmp_media_file, filepath)
    finally:
        if os.path.exists(tmp_chapter_file):
            os.remove(tmp_chapter_file)
        # Clean up temp media file if it exists
        if os.path.exists(tmp_media_file):
            os.remove(tmp_media_file)
        
