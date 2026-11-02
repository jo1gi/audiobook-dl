import os
import shutil
import subprocess

import pytest

from audiobookdl import AudiobookMetadata
from audiobookdl.output.output import gen_output_location, combine_audiofiles, _ffprobe_duration
from audiobookdl.output.download import get_output_audio_format

TEST_DATA = [
    {
        "template": "{author} - {title}",
        "metadata": AudiobookMetadata("The Way of Kings", authors = ["Brandon Sanderson"]),
        "remove_chars": "",
        "output": "Brandon Sanderson - The Way of Kings"
    },
    {
        "template": "{title}",
        "metadata": AudiobookMetadata("The Deal of a Lifetime: A Novella"),
        "remove_chars": ":,.",
        "output": "The Deal of a Lifetime A Novella",
    }
]

def test_gen_output_location():
    for test in TEST_DATA:
        assert gen_output_location(test["template"], test["metadata"], test["remove_chars"]) == test["output"]


def test_gen_output_audio_format_with_option():
    assert get_output_audio_format("m4b", ["file1.mp3","file2.mp3","file3.mp3"]) == ("mp3","m4b")


def test_gen_output_audio_format_without_option():
    assert get_output_audio_format(None, ["file1.mp3","file2.mp3","file3.mp3"]) == ("mp3", "mp3")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_combine_audiofiles_with_colon_in_directory(tmp_path, monkeypatch):
    # Paths are relative to the working directory, and ffmpeg reads "24:" as a protocol name
    monkeypatch.chdir(tmp_path)
    tmp_dir = "24: Title"
    os.mkdir(tmp_dir)
    parts = []
    for index in range(3):
        part = os.path.join(tmp_dir, f"Part {index}.aac")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency={440 + index * 100}:duration=2",
             "-c:a", "aac", f"file:{part}"],
            check=True, stdin=subprocess.DEVNULL,
        )
        parts.append(part)
    output_path = "24: Title.m4b"
    combine_audiofiles(parts, tmp_dir, output_path)
    assert _ffprobe_duration(output_path) == pytest.approx(6, abs=0.2)
