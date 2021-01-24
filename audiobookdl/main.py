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
    logging.set_loglevel(options.loglevel)
    logging.log("Checking for missing dependencies", "debug")
    missing = dependencies.check_dependencies(options)
    if not missing == True:
        logging.log(f"Missing dependency: {missing}", "error")
        exit(1)
    # Find service
    logging.log("Finding compatible service")
    s = find_compatible_service(options.url)
    if s == None:
        loggin.log("Could not find any mathing service", "error")
        exit()
    # Load cookie file
    if not options.cookie_file == None:
        s.load_cookie_file(options.cookie_file)
    # Download audiobook
    s.download(
        combine = options.combine,
        output_dir = options.output,
    )
