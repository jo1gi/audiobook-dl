import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Get list of items from scraped websites")
    parser.add_argument(
        'url',
        help="Url to download from"
    )
    parser.add_argument(
        '-c',
        '--cookies',
        dest='cookie_file',
        help="File with cookies",
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
            dest="output",
            help="Output folder",
            default="."
    )
    parser.add_argument(
        '--log-level',
        dest="loglevel",
        help="Log level",
        default="info",
    )
    parser.add_argument(
        '--print-output',
        dest="print_output",
        help="Prints the output locations instead of downloading",
        action='store_true',
    )
    return parser.parse_args()
