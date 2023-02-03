# Internal imports
from . import networking
from audiobookdl import logging, AudiobookFile
from audiobookdl.exceptions import DataNotPresent

# External imports
import requests
import lxml.html
from lxml.cssselect import CSSSelector
import re
from http.cookiejar import MozillaCookieJar
from typing import Any, Dict, List, Optional

class Source:
    """An abstract class for downloading audiobooks from a specific
    online source."""

    # A list of regexes that indicates which website a sevice supports
    match: List[str] = []
    # Methods for authenticating
    _authentication_methods: List[str] = [ "cookies" ]
    # Data required for logging in
    login_data: List[str] = [ "username", "password" ]
    # If cookies are loaded
    _authenticated = False
    # Cache of previously loaded pages
    _pages: Dict[str, bytes] = {}
    # List of names
    names: List[str] = []

    def __init__(self, url, match_num):
        self.url = url
        self.match_num = match_num
        self._session = requests.Session()

    @property
    def requires_authentication(self):
        """Returns `True` if this source requires authentication to download books"""
        return len(self._authentication_methods) > 0

    @property
    def authenticated(self):
        """Returns `True` if the source has been authenticated"""
        return self._authenticated

    @property
    def supports_cookies(self):
        return "cookies" in self._authentication_methods

    def load_cookie_file(self, cookie_file: str):
        """Loads cookies from a cookie file into session"""
        if self.supports_cookies:
            cookie_jar = MozillaCookieJar()
            cookie_jar.load(cookie_file, ignore_expires=True)
            self._session.cookies.update(cookie_jar)
            self._authenticated = True

    @property
    def supports_login(self):
        return "login" in self._authentication_methods

    def _login(self, username: str, password: str):
        pass

    def login(self, **kwargs):
        """Authenticate with source using username and password"""
        if self.supports_login:
            self._login(**kwargs)
            self._authenticated = True


    def before(self):
        """Operations to be run before the audiobook is downloaded"""
        pass

    def get_title(self) -> str:
        return ""

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata of the audiobook"""
        return {}

    def metadata(self) -> Dict[str, str]:
        m = self.get_metadata()
        if "authors" in m:
            m["author"] = "; ".join(m["authors"])
        if "narrators" in m:
            m["narrator"] = "; ".join(m["narrators"])
        return {
            **m,
            "title": self.get_title(),
            "genre": "Audiobook"
        }

    def get_cover(self) -> Optional[bytes]:
        """Returns the image data for the audiobook"""
        return None

    def get_cover_extension(self) -> str:
        """Returns the filetype of the cover from `get_cover`"""
        return "jpg"

    def get_files(self) -> List[AudiobookFile]:
        raise NotImplemented

    def get_chapters(self):
        """Returns a list of tuples with the starting point of the chapter and
        the title of the chapter"""
        pass


    def _get_page(self, url: str, **kwargs) -> bytes:
        """Downloads a page and caches it"""
        if url not in self._pages:
            resp = self.get(url, **kwargs)
            self._pages[url] = resp
        return self._pages[url]

    def find_elem_in_page(self, url, selector, data=None, **kwargs):
        """Finds an element in a page based on a css selector"""
        results = self.find_elems_in_page(url, selector, **kwargs)
        if len(results) == 0:
            logging.debug(f"Could not find matching element from {url} with {selector}")
            raise DataNotPresent
        elem = results[0]
        if data is None:
            return elem.text
        return elem.get(data)

    def find_elems_in_page(self, url, selector, **kwargs) -> List[Any]:
        sel = CSSSelector(selector)
        page: bytes = self._get_page(url, **kwargs)
        tree = lxml.html.fromstring(page.decode("utf8"))
        results = sel(tree)
        return results

    def find_in_page(self, url, regex, group_index=0, **kwargs) -> str:
        """Find some text in a page based on a regex"""
        m = re.search(regex, self._get_page(url, **kwargs).decode("utf8"))
        if m is None:
            logging.debug(f"Could not find match from {url} with {regex}")
            raise DataNotPresent
        return m.group(group_index)

    def find_all_in_page(self, url, regex, **kwargs):
        """Finds all places in a page that matches the regex"""
        return re.findall(regex, self._get_page(url, **kwargs).decode("utf8"))

    # Networking
    post = networking.post
    get = networking.get
    post_json = networking.post_json
    get_json = networking.get_json
    get_stream_files = networking.get_stream_files
