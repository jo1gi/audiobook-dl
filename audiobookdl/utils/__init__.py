import importlib.resources
from typing import Sequence
import shutil

def levenstein_distance(a: str, b: str) -> int:
    """
    Calculates the levenstein distance between `a` and `b`

    https://en.wikipedia.org/wiki/Levenshtein_distance
    """
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)
    if a[0] == b[0]:
        return levenstein_distance(a[1:], b[1:])
    return 1 + min(
        levenstein_distance(a, b[1:]), # Character is inserted
        levenstein_distance(a[1:], b), # Character is deleted
        levenstein_distance(a[1:], b[1:]) # Character is replaced
    )

def nearest_string(input: str, list: Sequence[str]) -> str:
    """
    Returns the closest element in `list` to `input` based on the levenstein
    distance
    """
    return sorted(list, key = lambda x: levenstein_distance(input, x))[0]


def read_asset_file(path: str) -> str:
    return importlib.resources.files("audiobookdl") \
        .joinpath(path) \
        .read_text(encoding="utf8")


def program_in_path(program: str) -> bool:
    """Checks whethher `program` is in the path"""
    return shutil.which(program) is not None
