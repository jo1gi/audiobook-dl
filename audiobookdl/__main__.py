from audiobookdl import Source, logging, args, output, __version__
from .exceptions import AudiobookDLException, BookNotReleased
from .utils.audiobook import Audiobook, Series
from .output.download import download
from .sources import find_compatible_source
from .config import load_config, Config, SourceConfig

import cloudscraper  # Aggiunto per gestire Cloudflare

import os
import sys
from rich.prompt import Prompt
from typing import List, Optional, Union


def main() -> None:
    # Parsing arguments
    options = args.parse_arguments()
    config = load_config(options.config_location)
    options.output_template = options.output_template or config.output_template
    options.database_directory = options.database_directory or config.database_directory
    options.skip_downloaded = options.skip_downloaded or config.skip_downloaded
    # Applying arguments as global constants
    logging.debug_mode = options.debug
    logging.quiet_mode = options.quiet
    logging.ffmpeg_output = options.ffmpeg_output or options.debug
    logging.debug(f"audiobook-dl {__version__}", remove_styling=True)
    logging.debug(f"python {sys.version}", remove_styling=True)
    urls = args.get_urls(options)
    if not urls:
        logging.simple_help()
        exit()
    for url in urls:
        try:
            process_url(url, options, config)
        except AudiobookDLException as e:
            e.print()
            if logging.debug_mode:
                logging.print_traceback()


def process_url(url: str, options, config: Config):
    """
    Process url based on cli options.
    Will by default download the audiobook the url is pointing to.

    :param url: Url to process
    :param options: Cli options
    :param config: Configuration file options
    """
    logging.log("Finding compatible source")
    source_class = find_compatible_source(url)
    source = source_class(options)
    if source.requires_authentication and not source.authenticated:
        authenticate(url, source, options, config)
    # Running program
    logging.debug(f"Downloading result of [underline]{url}")
    result = source.download(url)
    logging.log("") # Empty line
    if isinstance(result, Audiobook):
        logging.log(f"Downloading [blue]{result.title}[/] from [magenta]{source.name}[/]")
        process_audiobook(source, result, options)
    elif isinstance(result, Series):
        count = len(result.books)
        logging.log(
            f"Downloading [yellow not bold]{count}[/] books in [blue]{result.title}[/] from [magenta]{source.name}[/]")
        for book in result.books:
            try:
                audiobook = audiobook_from_series(source, book)
                process_audiobook(source, audiobook, options)
            except BookNotReleased:
                logging.log(f"Skipped [blue]{book}[/] (not released)")
                continue


def get_cookie_path(options, config: Optional[SourceConfig]) -> Optional[str]:
    """
    Find path to cookie file. The cookie files a looked for in cli arguments
    and in the current directory.

    :param options: Cli options
    :param config: Configuration for source
    :returns: Path to cookie file
    """
    if options.cookie_file is not None and os.path.exists(options.cookie_file):
        return options.cookie_file
    if config is not None and config.cookie_file is not None and os.path.exists(config.cookie_file):
        return config.cookie_file
    if os.path.exists("./cookies.txt"):
        return "./cookies.txt"
    return None


def get_or_ask(attr: str, hidden: bool, options, config: Optional[SourceConfig]) -> str:
    """
    Check for `attr` in cli options and config options.
    Ask the user for the value if it is not found.

    :param attr: Attribute to search for
    :param hidden: Should the user input be hidden (Used for passwords)
    :param options: Cli options
    :param config: Configuration for source
    :returns: `attr` value from either cli options, config options, or user input
    """
    config_value = getattr(config, attr, None)
    value: Optional[str] = getattr(options, attr, None) or config_value
    if value is None:
        return Prompt.ask(attr.capitalize(), password=hidden)
    return value


def login(url: str, source: Source, options, config: Optional[SourceConfig]):
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
        login_data[name] = get_or_ask(name, hidden, options, config)
    source.login(url, **login_data)


def authenticate(url: str, source: Source, options, config: Config):
    """
    Authenticate source

    :param url: Url of book the user is trying to download
    :param source: Source the book should be downloaded from
    :param options: Cli options
    :param config: Config file options
    """
    logging.log(f"Authenticating with [magenta]{source.name}[/]")
    source_config = config.sources.get(source.name)
    # Load cookie file
    cookie_path = get_cookie_path(options, source_config)
    if cookie_path is not None:
        source.load_cookie_file(cookie_path)
    # Authenticating with username and password
    if source.supports_login and not source.authenticated:
        login(url, source, options, source_config)


def audiobook_from_series(source: Source, book) -> Audiobook:
    """
    Make an audiobook object from book result in series

    :param source: Source book originates from
    :param book: Audiobook metadata or book id
    :returns: Audiobook
    """
    if isinstance(book, Audiobook):
        return book
    return source.download_from_id(book.id)


def process_audiobook(source: Source, audiobook: Audiobook, options) -> None:
    """
    Operate on audiobook based on cli arguments

    :param audiobook: Audiobook to operate on
    :param options: Cli options
    :returns: Nothing
    """
    if options.print_output:
        print_output(audiobook, options)
    elif options.cover:
        download_cover(audiobook)
    else:
        download(audiobook, options)
        source.on_download_complete(audiobook)



def print_output(audiobook: Audiobook, options) -> None:
    """Prints output location"""
    metadata = audiobook.metadata
    location = output.gen_output_location(options.output_template, metadata, options.remove_chars)
    print(location)


def download_cover(audiobook: Audiobook) -> None:
    """
    Download audiobook cover

    :param audiobook: Audiobook with cover
    """
    cover = audiobook.cover
    if cover:
        with open(f"cover.{cover.extension}", "wb") as f:
            f.write(cover.image)


if __name__ == "__main__":
    main()
