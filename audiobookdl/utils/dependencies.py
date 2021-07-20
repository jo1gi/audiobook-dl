import shutil


def program_in_path(program):
    """Checks if the given program is in the users path"""
    return shutil.which(program) is not None


def check_dependencies(options):
    """Checks if the required dependencies can be found"""
    required = {
            "combine": ["ffmpeg"]
            }
    for key, deps in required.items():
        if getattr(options, key):
            for i in deps:
                if not program_in_path(i):
                    return i
    return True
