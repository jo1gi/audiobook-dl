import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
            description="Download audiobooks from websites")
    parser.add_argument(
        'url',
        help="Url to download from"
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
        '--log-level',
        dest="loglevel",
        help="Log level (debug, info, warning, or error)",
        default="info",
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
        '--verbose-ffmpeg',
        dest="ffmpeg_output",
        help="Show ffmpeg output in terminal",
        action="store_true",
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
        help="File format to convert audio files to",
    )
    return parser.parse_args()
