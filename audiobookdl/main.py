from .services import get_service_classes
from .utils import args, dependencies, logging
import re, subprocess, os, shutil, rich

def find_compatible_service(url):
    """Finds the first service that supports the given url"""
    services = get_service_classes()
    for service in services:
        for n,m in enumerate(service.match):
            if not re.match(m, url) == None:
                return service(url, n)
    return None

def run():
    options = args.parse_arguments()
    missing = dependencies.check_dependencies(options)
    if not missing == True:
        logging.error(f"Missing dependency: {missing}")
        exit(1)
    # Find service
    logging.status("Finding compatible service")
    s = find_compatible_service(options.url)
    if s == None:
        loggin.error("Could not find any mathing service")
        exit()
    # Load cookie file
    if not options.cookie_file == None:
        s.load_cookie_file(options.cookie_file)
    # Download audiobook
    s.download(
        combine = options.combine,
    )
