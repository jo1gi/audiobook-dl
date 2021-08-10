import os
import subprocess


LOCATION_DEFAULTS = {
        'album': 'NA',
        'artist': 'NA',
        }


def gen_output_filename(booktitle, file, template):
    """Generates an output filename based on different attributes of the
    file"""
    arguments = {**file, **{"booktitle": booktitle}}
    filename = template.format(**arguments)
    return filename


def combine_audiofiles(filenames, tmp_dir, output_path):
    """Combines the given audiofiles in `path` into a new file"""
    combine_file = os.path.join(tmp_dir, "combine.txt")
    with open(combine_file, "a") as f:
        for i in filenames:
            f.write(f"file '{i}'\n")
    subprocess.run(
            ["ffmpeg", "-f", "concat", "-safe", "0", "-i",
                combine_file, "-c", "copy", output_path],
            capture_output=True)


def convert_output(paths):
    """Converts a list of audio files into another format"""
    pass


def gen_output_location(template, title, metadata):
    """Generates the location of the output based on attributes of the
    audiobook"""
    if metadata is None:
        metadata = {}
    metadata = {**LOCATION_DEFAULTS, **metadata}
    return template.format(
        title=title,
        **metadata
    )
