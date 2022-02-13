import re
from .sources.__init__ import get_source_classes
from .utils import args, dependencies, logging, output, messages
from .utils.exceptions import AudiobookDLException, NoSourceFound
from .utils.source import Source
from .download import download


def find_compatible_source(url: str) -> Source:
    """Finds the first source that supports the given url"""
    sources = get_source_classes()
    for source in sources:
        for n, m in enumerate(source.match):
            if not re.match(m, url) is None:
                return source(url, n)
    raise NoSourceFound


def run():
    """Main function"""
    # Parsing arguments
    options = args.parse_arguments()
    if options.url is None:
        messages.simple_help()
        exit()
    # Applying arguments as constants
    logging.set_loglevel(options.loglevel)
    output.ffmpeg_output = options.ffmpeg_output
    # Find source
    try:
        dependencies.check_dependencies(options)
        logging.log("Finding compatible source")
        s = find_compatible_source(options.url)
        # Load cookie file
        if options.cookie_file is not None:
            s.load_cookie_file(options.cookie_file)
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
    with open(f"cover.{ext}", "wb") as f:
        f.write(cover)

if __name__ == "__main__":
    run()
