from ..utils.service import Service

class BookbeatService(Service):
    require_cookies = True
    match = [
            r"https://"
            ]
