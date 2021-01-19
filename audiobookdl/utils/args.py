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
    return parser.parse_args()
