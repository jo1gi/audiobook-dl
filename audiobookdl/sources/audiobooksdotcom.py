from .source import Source
from audiobookdl import AudiobookFile, logging, AudiobookMetadata, Cover, Audiobook, Series, Result, BookId
from audiobookdl.exceptions import NoSourceFound, DataNotPresent, GenericAudiobookDLException
from rich.markup import escape

import re
from typing import List, Optional, Union
from urllib.parse import unquote
from urllib3.util import parse_url
import requests

BASEURL = "https://www.audiobooks.com/book/stream/"


class AudiobooksdotcomSource(Source):
    match = [
        r"{}\d+(/\d)?".format(BASEURL),
        r"https?://(www\.)?audiobooks\.com/audiobook/.+",
        r"https?://(www\.)?audiobooks\.com/browse/library.*",
    ]
    names = [ "audiobooks.com" ]

    def download(self, url: str) -> Result:
        path = parse_url(url).path
        if not path:
            raise NoSourceFound
        
        if "/browse/library" in path:
            # User-Agent has to match the one in the cookies for scraping library
            user_agent = self.extract_useragent_from_cookies()
            logging.debug(f"{user_agent=}")
            self._session.headers.update({"User-Agent": user_agent})
            return self.download_library(url)

        if "/book/stream/" in path:
            book_id = path.split("/")[3]
        elif "/audiobook/" in path:
            book_id = path.split("/")[-1]
        else:
            raise NoSourceFound
        return self.download_from_id(book_id)


    def download_from_id(self, book_id: str) -> Audiobook:
        # User-Agent has to match the one in the cookies
        user_agent = self.extract_useragent_from_cookies()
        logging.debug(f"{user_agent=}")
        self._session.headers.update({"User-Agent": user_agent})
        scrape_url = f"{BASEURL}{book_id}/1"
        return Audiobook(
            session = self._session,
            metadata = self.extract_metadata(scrape_url),
            cover = self.download_cover(scrape_url),
            files = self.extract_file(scrape_url),
        )


    def download_library(self, url: str) -> Series:
        logging.debug(f"Downloading library from {url}")
        book_ids = []
        page_url: Optional[str] = url
        
        # Keep scraping pages until there's no "next page" link
        while page_url:
            logging.debug(f"Scraping page {page_url}")
            book_links = self.find_elems_in_page(page_url, "div.book > a.no-decoration")
            for link in book_links:
                href = link.get("href")
                if href and "/audiobook/" in href:
                    book_id = href.split("/")[-1]
                    book_ids.append(book_id)
            
            # Find next page
            try:
                next_page_link = self.find_elem_in_page(page_url, "li.page-item.next > a.page-link", data="href")
                if next_page_link:
                    parsed_initial_url = parse_url(url)
                    page_url = f"{parsed_initial_url.scheme}://{parsed_initial_url.host}{next_page_link}"
                else:
                    page_url = None
            except DataNotPresent:
                page_url = None

        unique_book_ids = sorted(list(set(book_ids)))
        books = [BookId(book_id) for book_id in unique_book_ids]

        return Series(
            title = "audiobooks.com Library",
            books = books
        )


    def extract_metadata(self, scrape_url: str) -> AudiobookMetadata:
        title = self.find_elem_in_page(scrape_url, "h2#bookTitle")
        return AudiobookMetadata(title)


    def download_cover(self, scrape_url: str) -> Cover:
        cover_url = "https:" + \
            self.find_elem_in_page(
                scrape_url,
                "img.bookimage",
                data="src"
            )
        return Cover(self.get(cover_url), "jpg")


    def extract_useragent_from_cookies(self) -> str:
        """
        Extracts user agent from cookies in local session.

        :returns: User-Agent string
        """
        raw: Union[str, None] = self._session.cookies.get("ci_session", domain="www.audiobooks.com")
        if not raw:
            raise GenericAudiobookDLException(f"ci_session missing from cookie")
        else:
            decoded_cookie = unquote(raw)
            # The ci_session cookie is a serialized PHP array. We can extract the user_agent with a regex.
            match = re.search(r's:10:"user_agent";s:\d+:"([^"]+)";', decoded_cookie)
            if match:
                return match.group(1)
            # Fallback to old method if regex fails
            try:
                return decoded_cookie.split("\"")[11]
            except IndexError:
                raise GenericAudiobookDLException("Could not extract user_agent from ci_session cookie")


    def extract_file(self, scrape_url: str) -> List[AudiobookFile]:
        """
        Extract audio url from html page

        :param scrape_url: Url of page to scrape for audio link
        :returns: List of audio files with a single file in it
        """
        response = self._session.get(
            scrape_url,
        )
        audio_match = re.search(
            r'(?<=(mp3: "))[^"]+',
            response.text
        )
        if audio_match is None:
            logging.debug(f"Could not find audio URL. Page content from {scrape_url} was:\n{escape(response.text)}")
            raise DataNotPresent
        audio_url = audio_match.group()
        return [ AudiobookFile(url=audio_url, ext="mp3") ]
