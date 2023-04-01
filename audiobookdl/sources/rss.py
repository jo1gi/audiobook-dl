from .source import Source
import requests

class RssSource(Source):
    match = [ r"" ]
    names = [ "Rss" ]
    _authentication_methods: list[str] = []
