from .audiobooksdotcom import AudiobooksdotcomSource
from .chapter import ChapterSource
from .chirp import ChirpSource
from .ereolen import EreolenSource
from .librivox import LibrivoxSource
from .overdrive import OverdriveSource
from .scribd import ScribdSource
from .yourcloudlibrary import YourCloudLibrarySource

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
