# Internal imports
from .exceptions import CookiesNotLoadedException
from . import networking, metadata, output, logging

# External imports
import requests
import re
import shutil
import os
import rich
import lxml.html
from http.cookiejar import MozillaCookieJar
from lxml.cssselect import CSSSelector
from rich.progress import Progress


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

    def download_file(self, path, url, name, **kwargs):
        """Downloads a file to the correct output folder"""
        req = self._session.get(url, stream=True)
        with Progress() as progress:
            with open(path, "wb") as f:
                task = progress.add_task(
                        f"Downloading [blue]{name}[/blue]",
                        total=int(req.headers['Content-length']))
                for chunk in req.iter_content(chunk_size=1024):
                    f.write(chunk)
                    progress.update(task, advance=1024)

    def load_cookie_file(self, cookie_file):
        """Loads cookies from a cookie file into session"""
        cookie_jar = MozillaCookieJar()
        cookie_jar.load(cookie_file)
        self._session.cookies.update(cookie_jar)
        self._cookies_loaded = True

    def download_files(self, files, output_dir, **kwargs):
        """Downloads the given files and uses `**kwargs` as input to
        requests"""
        if len(files) > 1:
            self.setup_download_dir(output_dir)
            print(f"Downloading {len(files)} files")
            filenames = []
            for i in files:
                name = output.gen_output_filename(
                    self.title,
                    i,
                    "{booktitle} - Part {part}.{ext}"
                )
                path = os.path.join(output_dir, name)
                self.download_file(path, i["url"], name, **kwargs)
                if "title" in i:
                    metadata.add_metadata(path, {"title": i["title"]})
                filenames.append(name)
            return filenames
        elif len(files) == 1:
            print("Downloading 1 file")
            f = files[0]
            name = f"{self.title}.{f['ext']}"
            path = f"{output_dir}.{f['ext']}"
            self.download_file(path, f['url'], name, **kwargs)
            return [name]

    def before(self):
        """Operations to be run before the audiobook is downloaded"""
        pass

    def get_metadata(self):
        """Returns metadata of the audiobook"""
        pass

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

    def download(self, combine=False, output_template="{title}",
                 output_format="mp3"):
        """Downloads the audiobook from the given url"""
        if self.require_cookies and not self._cookies_loaded:
            raise CookiesNotLoadedException
        self.before()
        self.title = self.get_title()
        files = self.get_files()
        meta = self.get_metadata()
        output_dir = output.gen_output_location(
                output_template,
                self.title,
                meta)
        filenames = self.download_files(files, output_dir)
        if combine or len(filenames) == 1:
            output_file = f"{output_dir}.mp3"
            if len(filenames) > 1:
                logging.log("Combining files")
                output.combine_audiofiles(filenames, output_dir, output_file)
                shutil.rmtree(output_dir)
            if meta is not None:
                metadata.add_metadata(output_file, meta)
            cover = self.get_cover()
            if cover is not None:
                logging.log("Adding cover")
                metadata.embed_cover(output_file, cover)
            chapters = self.get_chapters()
            if chapters is not None:
                logging.log("Adding chapters")
                metadata.add_chapters(output_file, chapters)
        else:
            for i in filenames:
                metadata.add_metadata(os.path.join(output_dir, i), meta)
            cover = self.get_cover()
            if cover is not None:
                logging.log("Adding cover")
                cover_path = os.path.join(
                        output_dir,
                        f"cover.{self.get_cover_filetype()}")
                with open(cover_path, 'wb') as f:
                    f.write(cover)

    def setup_download_dir(self, path):
        """Creates output folder"""
        if os.path.isdir(path):
            rich.print(f"The folder '{path}' already exists. Do you want to\
                    remove the files inside? [Y/n] ", end="")
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
