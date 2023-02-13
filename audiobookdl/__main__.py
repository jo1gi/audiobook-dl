from audiobookdl import Source, logging, args, output
from audiobookdl.exceptions import AudiobookDLException
from .utils import dependencies
from .output.download import download
from .sources import find_compatible_source

import os
import sys
from rich.prompt import Prompt

def get_cookie_path(options):
    """Find path to cookie file"""
    if options.cookie_file is not None and os.path.exists(options.cookie_file):
        return options.cookie_file
    if os.path.exists("./cookies.txt"):
        return "./cookies.txt"

def get_or_ask(name: str, hidden: bool, options) -> str:
    """Return `value` if it exists else asks for a value"""
    if hasattr(options, name) and getattr(options, name):
        return getattr(options, name)
    return Prompt.ask(name.capitalize(), password=hidden)

def login(source: Source, options):
    login_data = {}
    for name in source.login_data:
        hidden = name == "password"
        login_data[name] = get_or_ask(name, hidden, options)
    source.login(**login_data)

def get_urls(options):
    urls = []
    # Args
    urls.extend(options.urls)
    # File
    if options.input_file:
        with open(options.input_file, "r") as f:
            urls.extend(f.read().split())
    return urls

def run():
    """Main function"""
    # Parsing arguments
    options = args.parse_arguments()
    # Applying arguments as global constants
    logging.debug_mode = options.debug
    logging.quiet_mode = options.quiet
    logging.ffmpeg_output = options.ffmpeg_output or options.debug
    urls = get_urls(options)
    if not urls:
        logging.simple_help()
        exit()
    try:
        dependencies.check_dependencies(options)
        for url in urls:
            run_on_url(options, url)
    except AudiobookDLException as e:
        e.print()
        exit(1)

def run_on_url(options, url: str):
    logging.log("Finding compatible source")
    s = find_compatible_source(url)
    # Load cookie file
    cookie_path = get_cookie_path(options)
    if cookie_path is not None:
        s.load_cookie_file(cookie_path)
    # Adding username and password
    if s.supports_login and not s.authenticated:
        login(s, options)
    # Running program
    if options.print_output:
        print_output(s, options)
    elif options.cover:
        download_cover(s)
    else:
        download(s, options)


def print_output(source: Source, options):
    """Prints output location"""
    source.before()
    meta = source.get_metadata()
    location = output.gen_output_location(options.template, meta, options.remove_chars)
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
