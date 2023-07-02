import argparse
from audiobookdl import __version__
from typing import Any, List


def parse_arguments() -> Any:
    parser = argparse.ArgumentParser(
        prog="audiobook-dl",
        description="Download audiobooks from websites",
    )
    parser.add_argument(
        '-v',
        '--version',
        action = "version",
        version = f"audiobook-dl {__version__}"
    )
    parser.add_argument(
        'urls',
        help="Urls to download from",
        nargs='*',
    )
    parser.add_argument(
        '-c',
        '--cookies',
        dest='cookie_file',
        help="Path to Netscape cookie file",
    )
    parser.add_argument(
        '--combine',
        dest='combine',
        action='store_true',
        help="Combine output files into a single file",
    )
    parser.add_argument(
        '-o',
        '--output',
        dest="output_template",
        help="Output location",
        default="{title}"
    )
    parser.add_argument(
        '--remove-chars',
        dest="remove_chars",
        help = "List of characters that will be removed from output path",
        default="",
    )
    parser.add_argument(
        '--debug',
        '-d',
        dest="debug",
        help="Debug mode",
        action="store_true",
    )
    parser.add_argument(
        '--quiet',
        '-q',
        dest="quiet",
        help="Quiet mode",
        action="store_true",
    )
    parser.add_argument(
        '--print-output',
        dest="print_output",
        help="Prints the output locations instead of downloading",
        action='store_true',
    )
    parser.add_argument(
        '--cover',
        dest="cover",
        help="Download only cover",
        action='store_true',
    )
    parser.add_argument(
        '--no-chapters',
        dest="no_chapters",
        help="Don't include chapters in final file",
        action="store_true"
    )
    parser.add_argument(
        '-f',
        '--output-format',
        dest="output_format",
        help="Output file format",
    )
    parser.add_argument(
        '--verbose-ffmpeg',
        dest="ffmpeg_output",
        help="Show ffmpeg output in terminal",
        action="store_true",
    )
    parser.add_argument(
        '--input-file',
        dest="input_file",
        help="File with one url to download per line",
    )
    parser.add_argument(
        '--username',
        dest="username",
        help="Username for source",
    )
    parser.add_argument(
        '--password',
        dest="password",
        help="Password for source",
    )
    parser.add_argument(
        '--library',
        dest="library",
        help="Library for source",
    )
    parser.add_argument(
        '--write-json-metadata',
        dest = "write_json_metadata",
        help = "Write metadata in a seperate json file",
        action="store_true",
    )
    parser.add_argument(
        '--config',
        dest = "config_location",
        help = "Alternative location of config file"
    )
    return parser.parse_args()


def get_urls(options) -> List[str]:
    """
    Creates a list of all urls in cli options.
    Urls a found in `options.urls` and read from `options.input_file` if the
    file exists

    :param options: Cli options
    :returns: Combined list of all urls
    """
    urls = []
    # Args
    urls.extend(options.urls)
    # File
    if options.input_file:
        with open(options.input_file, "r") as f:
            urls.extend(f.read().split())
    return urls
