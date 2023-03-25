import shutil
from audiobookdl import logging
from audiobookdl.exceptions import MissingDependency


def program_in_path(program) -> bool:
    """Checks if the given program is in the users path"""
    return shutil.which(program) is not None


def check_dependencies(options) -> None:
    """Checks if the required dependencies can be found"""
    required = {
        "combine": ["ffmpeg"]
    }
    logging.debug("Searching for missing dependencies")
    for key, deps in required.items():
        if getattr(options, key):
            for i in deps:
                if not program_in_path(i):
                    raise MissingDependency(dependency=i)
