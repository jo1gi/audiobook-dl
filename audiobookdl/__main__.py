from audiobookdl import Source, logging, args, output, __version__, Audiobook
from audiobookdl.exceptions import AudiobookDLException
from .utils import dependencies
from .output.download import download
from .sources import find_compatible_source
from .config import load_config, Config

import os
import sys
from rich.prompt import Prompt
from typing import List, Optional
import traceback

def get_cookie_path(options) -> Optional[str]:
    """Find path to cookie file"""
    if options.cookie_file is not None and os.path.exists(options.cookie_file):
        return options.cookie_file
    if os.path.exists("./cookies.txt"):
        return "./cookies.txt"
    return None


def get_or_ask(attr: str, hidden: bool, source_name: str, options, config: Config) -> str:
    """
    Check for `attr` in cli options and config options.
    Ask the user for the value if it is not found.

    :param attr: Attribute to search for
    :param hidden: Should the user input be hidden (Used for passwords)
    :param source_name: Name of source
    :param options: Cli options
    :param config: Config file options
    :returns: `attr` value from either cli options, config options, or user input
    """
    config_value = getattr(config.sources.get(source_name), attr, None)
    value: Optional[str] = getattr(options, attr, None) or config_value
    if value is None:
        return Prompt.ask(attr.capitalize(), password=hidden)
    return value


def login(url: str, source: Source, options, config: Config):
    """
    Login to source

    :param url: Url for book
    :param source: Source the user is trying to login to
    :param options: Cli options
    :param config: Config file options
    """
    login_data = {}
    for name in source.login_data:
        hidden = name == "password"
        login_data[name] = get_or_ask(name, hidden, source.name, options, config)
    source.login(url, **login_data)


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


def run() -> None:
    """Main function"""
    # Parsing arguments
    options = args.parse_arguments()
    config = load_config(options.config_location)
    options.output_template = options.output_template or config.output_template
    # Applying arguments as global constants
    logging.debug_mode = options.debug
    logging.quiet_mode = options.quiet
    logging.ffmpeg_output = options.ffmpeg_output or options.debug
    logging.debug(f"audiobook-dl {__version__}", remove_styling=True)
    logging.debug(f"python {sys.version}", remove_styling=True)
    urls = get_urls(options)
    if not urls:
        logging.simple_help()
        exit()
    try:
        dependencies.check_dependencies(options)
        for url in urls:
            run_on_url(url, options, config)
    except AudiobookDLException as e:
        e.print()
        traceback.print_exc()
        exit(1)


def run_on_url(url: str, options, config: Config):
    logging.log("Finding compatible source")
    source = find_compatible_source(url)
    # Load cookie file
    cookie_path = get_cookie_path(options)
    if cookie_path is not None:
        source.load_cookie_file(cookie_path)
    # Authenticating with username and password
    if source.supports_login and not source.authenticated:
        login(url, source, options, config)
    # Running program
    audiobook = source.download(url)
    if not isinstance(audiobook, Audiobook):
        raise NotImplementedError
    if options.print_output:
        print_output(url, source, options)
    elif options.cover:
        download_cover(url, source)
    else:
        download(audiobook, options)


def print_output(url: str, source: Source, options):
    """Prints output location"""
    audiobook = source.download(url)
    if isinstance(audiobook, Audiobook):
        metadata = audiobook.metadata
        location = output.gen_output_location(options.template, metadata, options.remove_chars)
        print(location)
    else:
        raise NotImplementedError


def download_cover(url: str, source: Source):
    audiobook = source.download(url)
    if isinstance(audiobook, Audiobook):
        cover = audiobook.cover
        if cover:
            with open(f"cover.{cover.extension}", "wb") as f:
                f.write(cover.image)
    else:
        raise NotImplementedError


if __name__ == "__main__":
    run()
