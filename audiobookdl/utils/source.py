# Internal imports
from . import networking, output, metadata, logging
from .exceptions import RequestError, DataNotPresent

# External imports
import requests
import shutil
import lxml.html
from lxml.cssselect import CSSSelector
import os
import re
from http.cookiejar import MozillaCookieJar
from rich.progress import Progress, BarColumn
from rich.prompt import Confirm
from typing import Dict, List
from multiprocessing.pool import ThreadPool
from functools import partial
from Crypto.Cipher import AES

class Source:
    """An abstract class for downloading audiobooks from a specific
    online source."""

    # A list of regexes that indicates which website a sevice supports
    match: List[str] = []
    # If cookies need to be loaded to be able to use source
    require_cookies = False
    # If cookies are loaded
    _cookies_loaded = False
    # Cache of previously loaded pages
    _pages: Dict[str, bytes] = {}

    def __init__(self, url, match_num):
        self.url = url
        self.match_num = match_num
        self._session = requests.Session()

    def load_cookie_file(self, cookie_file):
        """Loads cookies from a cookie file into session"""
        cookie_jar = MozillaCookieJar()
        cookie_jar.load(cookie_file, ignore_expires=True)
        self._session.cookies.update(cookie_jar)
        self._cookies_loaded = True

    def create_filename(self, length, output_dir, file):
        if length == 1:
            name = f"{self.title}.{file['ext']}"
            path = f"{output_dir}.{file['ext']}"
        else:
            name = output.gen_output_filename(
                self.title,
                file,
                "{booktitle} - Part {part}.{ext}"
            )
            path = os.path.join(output_dir, name)
        return name, path

    def download_file(self, args):
        file, length, output_dir, progress = args
        name, path = self.create_filename(length, output_dir, file)
        headers = {} if "headers" not in file else file["headers"]
        req = self._session.get(file["url"], headers=headers, stream=True)
        file_size = int(req.headers["Content-length"])
        total = 0
        with open(path, "wb") as f:
            for chunk in req.iter_content(chunk_size=1024):
                f.write(chunk)
                new = len(chunk)/file_size
                total += new
                progress(new)
        progress(1-total)
        if "encryption_key" in file:
            with open(path, "rb") as f:
                cipher = AES.new(
                    file["encryption_key"],
                    AES.MODE_CBC,
                    file["iv"]
                )
                decrypted = cipher.decrypt(f.read())
            with open(path, "wb") as f:
                f.write(decrypted)
        metadata.add_metadata(path, file)
        return name

    def download_files(self, files, output_dir):
        self.setup_download_dir(output_dir)
        info = [
            "{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%"
        ]
        with Progress(*info) as progress:
            task = progress.add_task(
                f"Downloading {len(files)} files - [blue]{self.title}",
                total = len(files)
            )
            # Downloading files
            filenames = []
            p = partial(progress.advance, task)
            with ThreadPool(processes=20) as pool:
                for i in pool.imap(self.download_file, [(f, len(files), output_dir, p) for f in files]):
                    filenames.append(i)
            # Making sure progress is completed
            remaining = progress.tasks[0].remaining
            progress.advance(task, remaining)
            return filenames

    def before(self):
        """Operations to be run before the audiobook is downloaded"""
        pass

    def get_title(self) -> str:
        return ""

    @property
    def title(self) -> str:
        return self.get_title()

    def get_metadata(self) -> Dict[str, str]:
        """Returns metadata of the audiobook"""
        return {}

    @property
    def metadata(self) -> Dict[str, str]:
        m = self.get_metadata()
        if "authors" in m:
            m["author"] = "; ".join(m["authors"])
        if "narrators" in m:
            m["narrator"] = "; ".join(m["narrators"])
        return {
            **m,
            "title": self.title,
            "genre": "Audiobook"
        }

    def get_cover(self) -> bytes:
        """Returns the image data for the audiobook"""
        raise NotImplementedError

    def get_cover_extension(self) -> str:
        """Returns the filetype of the cover from `get_cover`"""
        return "jpg"

    def get_files(self) -> List[Dict[str, str]]:
        raise NotImplemented

    def get_chapters(self):
        """Returns a list of tuples with the starting point of the chapter and
        the title of the chapter"""
        pass

    def setup_download_dir(self, path):
        """Creates output folder"""
        if os.path.isdir(path):
            answer = Confirm.ask(f"The folder '{path}' already exists. Do you want to override it?")
            if answer:
                shutil.rmtree(path)
            else:
                exit()
        os.makedirs(path)

    def _get_page(self, url: str, **kwargs) -> bytes:
        """Downloads a page and caches it"""
        if url not in self._pages:
            resp = self._session.get(url, **kwargs).content
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

    def find_elems_in_page(self, url, selector, **kwargs):
        sel = CSSSelector(selector)
        page = self._get_page(url, **kwargs)
        if page is None:
            return []
        tree = lxml.html.fromstring(page.decode("utf8"))
        results = sel(tree)
        return results

    def find_in_page(self, url, regex, **kwargs):
        """Find some text in a page based on a regex"""
        m = re.search(regex, self._get_page(url, **kwargs).decode("utf8"))
        if m is None:
            logging.debug(f"Could not find match from {url} with {regex}")
            raise DataNotPresent
        return m.group(0)

    def find_all_in_page(self, url, regex, **kwargs):
        """Finds all places in a page that matches the regex"""
        return re.findall(regex, self._get_page(url, **kwargs).decode("utf8"))

    # Networking
    post = networking.post
    get = networking.get
    post_json = networking.post_json
    get_json = networking.get_json
    get_stream_files = networking.get_stream_files
