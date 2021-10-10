# Internal imports
from . import networking, output
from ..download import DownloadThread

# External imports
import requests
import re
import shutil
import os
import rich
import lxml.html
from http.cookiejar import MozillaCookieJar
from lxml.cssselect import CSSSelector
from rich.progress import Progress, BarColumn


class Service:
    """An abstract class for downloading audiobooks from a specific
    online service."""

    # A list of regexes that indicates which website a sevice supports
    match = []
    # If cookies need to be loaded to be able to use service
    require_cookies = False
    # If cookies are loaded
    _cookies_loaded = False
    # Cache of previously loaded pages
    _pages = {}
    title = None

    def __init__(self, url, match_num):
        self.url = url
        self.match_num = match_num
        self._session = requests.Session()

    def load_cookie_file(self, cookie_file):
        """Loads cookies from a cookie file into session"""
        cookie_jar = MozillaCookieJar()
        cookie_jar.load(cookie_file)
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

    def download_files(self, files, output_dir, **kwargs):
        """Downloads the given files and uses `**kwargs` as input to
        requests"""
        self.setup_download_dir(output_dir)
        info = [
            "{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%"
        ]
        with Progress(*info) as progress:
            # Creating progress bar
            task = progress.add_task(
                f"Downloading {len(files)} file(s) - [blue]{self.title}",
            )
            # Adding download data for all files
            total = 0
            filenames = []
            threads = []
            for n, file in enumerate(files):
                name, path = self.create_filename(len(files), output_dir, file)
                filenames.append(name)
                t = DownloadThread(self._session,
                                   path, file["url"], file, progress, task)
                t.start()
                total += t.get_length()
                progress.update(task, total=len(files)*(total/(n+1)))
                threads.append(t)
            # Setting total time of progress bar
            # Starting thread
            # Waiting for threads
            for t in threads:
                t.join()
            return filenames

    def before(self):
        """Operations to be run before the audiobook is downloaded"""
        pass

    def after(self):
        """Operations to be run after the audiobook is downloaded"""
        pass

    def get_metadata(self):
        """Returns metadata of the audiobook"""
        return {}

    def get_cover(self):
        """Returns the image data for the audiobook"""
        pass

    def get_cover_filetype(self):
        """Returns the filetype of the cover from `get_cover`"""
        return "jpg"

    def get_chapters(self):
        """Returns a list of tuples with the starting point of the chapter and
        the title of the chapter"""
        pass

    def setup_download_dir(self, path):
        """Creates output folder"""
        if os.path.isdir(path):
            rich.print(f"The folder '{path}' already exists. Do you want to override it? [Y/n] ", end="")
            answer = input()
            if answer.lower == 'y' or answer == '':
                shutil.rmtree(path)
            else:
                exit()
        os.makedirs(path)

    def _get_page(self, url, **kwargs):
        """Downloads a page and caches it"""
        if url not in self._pages:
            resp = self._session.get(url, **kwargs).content
            if resp is None:
                return None
            self._pages[url] = resp.decode('utf8')
        return self._pages[url]

    def find_elem_in_page(self, url, selector, data=None, **kwargs):
        """Finds an element in a page based on a css selector"""
        sel = CSSSelector(selector)
        page = self._get_page(url, **kwargs)
        if page is None:
            return None
        tree = lxml.html.fromstring(page)
        results = sel(tree)
        if len(results) == 0:
            return None
        elem = results[0]
        if data is None:
            return elem.text
        return elem.get(data)

    def find_in_page(self, url, regex, **kwargs):
        """Find some text in a page based on a regex"""
        m = re.search(regex, self._get_page(url, **kwargs))
        if m is None:
            return None
        return m.group(0)

    def find_all_in_page(self, url, regex, **kwargs):
        """Finds all places in a page that matches the regex"""
        return re.findall(regex, self._get_page(url, **kwargs))

    # Networking
    post = networking.post
    get = networking.get
    post_json = networking.post_json
    get_json = networking.get_json
