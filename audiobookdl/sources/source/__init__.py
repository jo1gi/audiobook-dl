# Internal imports
from . import networking
from audiobookdl import logging, AudiobookFile, Chapter, AudiobookMetadata, Cover, Result, Audiobook, BookId
from audiobookdl.exceptions import DataNotPresent

# External imports
import requests
import lxml.html
from lxml.cssselect import CSSSelector
import re
from http.cookiejar import MozillaCookieJar
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar("T")

class Source(Generic[T]):
    """An abstract class for downloading audiobooks from a specific
    online source."""

    # Data required for logging in
    login_data: List[str] = [ "username", "password" ]
    # A list of regexes that indicates which website a sevice supports
    match: List[str] = []
    # list of names
    names: List[str] = []
    # Methods for authenticating
    _authentication_methods: List[str] = [ "cookies" ]
    # If cookies are loaded
    __authenticated = False
    # Cache of previously loaded pages
    __pages: Dict[str, bytes] = {}


    def __init__(self):
        self._session = requests.Session()


    @property
    def name(self) -> str:
        """Primary name of source"""
        return self.names[0].lower()


    @property
    def requires_authentication(self):
        """Returns `True` if this source requires authentication to download books"""
        return len(self._authentication_methods) > 0


    @property
    def authenticated(self):
        """Returns `True` if the source has been authenticated"""
        return self.__authenticated


    @property
    def supports_cookies(self):
        """Returns `True` if the source supports authentication with cookies"""
        return "cookies" in self._authentication_methods


    def load_cookie_file(self, cookie_file: str):
        """Loads cookies from a cookie file into session"""
        if self.supports_cookies:
            logging.debug(f"Loading cookies from '{cookie_file}'")
            cookie_jar = MozillaCookieJar()
            cookie_jar.load(cookie_file, ignore_expires=True)
            self._session.cookies.update(cookie_jar)
            self.__authenticated = True


    @property
    def supports_login(self):
        """Returns `True` if the source supports authentication with login"""
        return "login" in self._authentication_methods


    def _login(self, url: str, username: str, password: str):
        pass


    def login(self, url: str, **kwargs) -> None:
        """Authenticate with source using username and password"""
        if self.supports_login:
            logging.debug("Logging in")
            self._login(url, **kwargs)
            self.__authenticated = True


    def download_from_id(self, book_id: T) -> Audiobook:
        """Download book specified by id"""
        raise NotImplementedError


    def download(self, url: str) -> Result:
        """Download book or series"""
        raise NotImplementedError


    def _get_page(self, url: str, use_cache: bool = True, **kwargs) -> bytes:
        """Download a page and caches it"""
        if url not in self.__pages and use_cache:
            resp = self.get(url, **kwargs)
            if use_cache:
                self.__pages[url] = resp
        return self.__pages[url]


    def find_elem_in_page(self, url: str, selector: str, data=None, **kwargs):
        """
        Find the first html element in page from `url` that matches `selector`.
        Will return the attribute specified in `data`. Will return element text
        if `data` is `None`.
        Will cache the page.
        """
        results = self.find_elems_in_page(url, selector, **kwargs)
        if len(results) == 0:
            logging.debug(f"Could not find matching element from {url} with {selector}")
            raise DataNotPresent
        elem = results[0]
        if data is None:
            return elem.text
        return elem.get(data)


    def find_elems_in_page(self, url: str, selector: str, **kwargs) -> list:
        """
        Find all html elements in the page from `url` thats matches `selector`.
        Will cache the page.
        """
        sel = CSSSelector(selector)
        page: bytes = self._get_page(url, **kwargs)
        tree = lxml.html.fromstring(page.decode("utf8"))
        results = sel(tree)
        return results


    def find_in_page(self, url: str, regex: str, group_index: int = 0, **kwargs) -> str:
        """
        Find some text in a page based on a regex.
        Will cache the page.
        """
        page = self._get_page(url, **kwargs).decode("utf8")
        m = re.search(regex, page)
        if m is None:
            logging.debug(f"Could not find match from {url} with {regex}")
            raise DataNotPresent
        return m.group(group_index)


    def find_all_in_page(self, url: str, regex: str, **kwargs) -> list:
        """
        Find all places in a page that matches the regex.
        Will cache the page.
        """
        return re.findall(regex, self._get_page(url, **kwargs).decode("utf8"))

    # Networking
    post = networking.post
    get = networking.get
    post_json = networking.post_json
    get_json = networking.get_json
    get_stream_files = networking.get_stream_files
