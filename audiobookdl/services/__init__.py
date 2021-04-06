from .services import *
def get_service_classes():
    return [
        klass
        for name, klass in globals().items()
        if name.endswith('Service')
    ]
