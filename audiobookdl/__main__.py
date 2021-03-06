from .services.__init__ import get_service_classes
from .utils import args, dependencies, logging, output
import re, subprocess, os, shutil, rich
from .utils.exceptions import UserNotAuthenticated

def find_compatible_service(url):
    """Finds the first service that supports the given url"""
    services = get_service_classes()
    for service in services:
        for n,m in enumerate(service.match):
            if not re.match(m, url) == None:
                return service(url, n)
    return None

def run():
    """Main function"""
    options = args.parse_arguments()
    logging.set_loglevel(options.loglevel)
    if options.print_output:
        logging.set_loglevel("error")
    logging.log("Checking for missing dependencies", "debug")
    missing = dependencies.check_dependencies(options)
    if not missing == True:
        logging.log(f"Missing dependency: {missing}", "error")
        exit(1)
    # Find service
    logging.log("Finding compatible service")
    s = find_compatible_service(options.url)
    if s == None:
        logging.log("Could not find any mathing service", "error")
        exit()
    # Load cookie file
    if not options.cookie_file == None:
        s.load_cookie_file(options.cookie_file)
    if options.print_output:
        print_output(s, options.output)
        exit()
    # Download audiobook
    try:
        s.download(
                combine = options.combine,
                output_template = options.output,
                )
    except UserNotAuthenticated:
        logging.error("Authentication did not work correctly")

def print_output(service, template):
    """Prints output location"""
    service.before()
    title = service.get_title()
    meta = service.get_metadata()
    location = output.gen_output_location(template, title, meta)
    print(location)

if __name__ == "__main__":
    run()
