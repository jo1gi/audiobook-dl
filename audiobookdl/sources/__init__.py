from .sources import *


def get_source_classes():
    return [
        klass
        for name, klass in globals().items()
        if name.endswith('Source')
    ]
