from audiobookdl import Source, logging, args, output
from audiobookdl.exceptions import AudiobookDLException, NoSourceFound
from .utils import dependencies
from .output.download import download
from .sources import get_source_classes

import os
import re
from rich.prompt import Prompt
from typing import Optional


def find_compatible_source(url: str) -> Source:
    """Finds the first source that supports the given url"""
    sources = get_source_classes()
    for source in sources:
        for n, m in enumerate(source.match):
            if not re.match(m, url) is None:
                return source(url, n)
    raise NoSourceFound


def get_cookie_path(options):
    """Find path to cookie file"""
    if options.cookie_file is not None and os.path.exists(options.cookie_file):
        return options.cookie_file
    if os.path.exists("./cookies.txt"):
        return "./cookies.txt"

def get_or_ask(value: Optional[str], name: str, hidden: bool) -> str:
    """Return `value` if it exists else asks for a value"""
    if value:
        return value
    return Prompt.ask(name, password=hidden)

def run():
    """Main function"""
    # Parsing arguments
    options = args.parse_arguments()
    if options.url is None:
        logging.simple_help()
        exit()
    # Applying arguments as global constants
    logging.debug_mode = options.debug
    logging.quiet_mode = options.quiet
    logging.ffmpeg_output = options.ffmpeg_output or options.debug
    try:
        dependencies.check_dependencies(options)
        logging.log("Finding compatible source")
        s = find_compatible_source(options.url)
        # Load cookie file
        cookie_path = get_cookie_path(options)
        if cookie_path is not None:
            s.load_cookie_file(cookie_path)
        # Adding username and password
        if s.require_username_and_password and cookie_path is None:
            s.username = get_or_ask(options.username, "Username", False)
            s.password = get_or_ask(options.password, "Password", True)
        # Running program
        if options.print_output:
            print_output(s, options.output)
        elif options.cover:
            download_cover(s)
        else:
            download(s, options)
    except AudiobookDLException as e:
        e.print()
        exit(1)


def print_output(source: Source, template: str):
    """Prints output location"""
    source.before()
    meta = source.get_metadata()
    location = output.gen_output_location(template, meta)
    print(location)


def download_cover(source: Source):
    source.before()
    ext = source.get_cover_extension()
    cover = source.get_cover()
    if cover:
        with open(f"cover.{ext}", "wb") as f:
            f.write(cover)

if __name__ == "__main__":
    run()
