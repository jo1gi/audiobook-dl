from .source import Source

from .audiobooksdotcom import AudiobooksdotcomSource
from .chapter import ChapterSource
from .chirp import ChirpSource
from .ereolen import EreolenSource
from .librivox import LibrivoxSource
from .overdrive import OverdriveSource
from .scribd import ScribdSource
from .yourcloudlibrary import YourCloudLibrarySource

from ..exceptions import NoSourceFound
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
        OverdriveSource,
        ScribdSource,
        YourCloudLibrarySource,
    ]
