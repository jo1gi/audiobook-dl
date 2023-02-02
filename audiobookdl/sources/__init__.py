from .source import Source

from .audiobooksdotcom import AudiobooksdotcomSource
from .chapter import ChapterSource
from .chirp import ChirpSource
from .ereolen import EreolenSource
from .librivox import LibrivoxSource
from .nextory import NextorySource
from .overdrive import OverdriveSource
from .scribd import ScribdSource
from .storytel import StorytelSource
from .yourcloudlibrary import YourCloudLibrarySource

from ..exceptions import NoSourceFound
from typing import List
import re

def find_compatible_source(url: str) -> Source:
    """Finds the first source that supports the given url"""
    sources = get_source_classes()
    for source in sources:
        for n, m in enumerate(source.match):
            if not re.match(m, url) is None:
                return source(url, n)
    raise NoSourceFound

def get_source_classes():
    """Returns a list of all available sources"""
    return [
        AudiobooksdotcomSource,
        ChapterSource,
        ChirpSource,
        EreolenSource,
        LibrivoxSource,
        NextorySource,
        OverdriveSource,
        ScribdSource,
        StorytelSource,
        YourCloudLibrarySource,
    ]

def get_source_names() -> List[str]:
    results: List[str] = []
    for source in get_source_classes():
        for source_name in source.names:
            results.append(source_name)
    return sorted(results, key=lambda x: x.lower())
