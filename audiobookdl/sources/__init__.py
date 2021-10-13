from .sources import *


def get_source_classes():
    """Returns a list of all available sources"""
    return [
        klass
        for name, klass in globals().items()
        if name.endswith('Source')
    ]
