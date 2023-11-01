from .source import Source

from .audiobooksdotcom import AudiobooksdotcomSource
from .blinkist import BlinkistSource
from .bookbeat import BookBeatSource
from .chirp import ChirpSource
from .ereolen import EreolenSource
from .librivox import LibrivoxSource
from .nextory import NextorySource
from .overdrive import OverdriveSource
from .podimo import PodimoSource
from .saxo import SaxoSource
from .everand import EverandSource
from .storytel import StorytelSource
from .yourcloudlibrary import YourCloudLibrarySource

from ..exceptions import NoSourceFound
import re
from typing import Iterable, List

def find_compatible_source(url: str) -> Source:
    """Finds the first source that supports the given url"""
    sources = get_source_classes()
    for source in sources:
        for n, m in enumerate(source.match):
            if not re.match(m, url) is None:
                return source()
    raise NoSourceFound


def get_source_classes():
    """Returns a list of all available sources"""
    return [
        AudiobooksdotcomSource,
        BlinkistSource,
        BookBeatSource,
        ChirpSource,
        EreolenSource,
        LibrivoxSource,
        NextorySource,
        OverdriveSource,
        PodimoSource,
        SaxoSource,
        EverandSource,
        StorytelSource,
        YourCloudLibrarySource,
    ]


def get_source_names() -> Iterable[str]:
    """
    Returns the names of all sources available
    There are sometimes multiple names for the same source
    """
    results: List[str] = []
    for source in get_source_classes():
        for source_name in source.names:
            results.append(source_name)
    return sorted(results, key=lambda x: x.lower())
