from .source import Source
from audiobookdl import AudiobookFile, logging, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import NoSourceFound, DataNotPresent

import re
from typing import List
from urllib.parse import unquote
from urllib3.util import parse_url
import requests

BASEURL = "https://www.audiobooks.com/book/stream/"


class AudiobooksdotcomSource(Source):
    match = [
        r"{}\d+(/\d)?".format(BASEURL)
    ]
    names = [ "audiobooks.com" ]

    def download(self, url: str) -> Audiobook:
        path = parse_url(url).path
        if not path:
            raise NoSourceFound
        # User-Agent has to match the one in the cookies
        user_agent = self.extract_useragent_from_cookies()
        logging.debug(f"{user_agent=}")
        self._session.headers.update({"User-Agent": user_agent})
        book_id = path.split("/")[3]
        scrape_url = f"{BASEURL}{book_id}/1"
        return Audiobook(
            session = self._session,
            metadata = self.extract_metadata(scrape_url),
            cover = self.download_cover(scrape_url),
            files = self.extract_file(scrape_url),
        )


    def extract_metadata(self, scrape_url: str) -> AudiobookMetadata:
        title = self.find_elem_in_page(scrape_url, "h2#bookTitle")
        return AudiobookMetadata(title)


    def download_cover(self, scrape_url: str) -> Cover:
        cover_url = "http:" + \
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
        raw = self._session.cookies.get("ci_session", domain="www.audiobooks.com")
        return unquote(raw).split("\"")[11]


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
            r'(?<=(mp3: ")).+(?=(&rs))',
            response.text
        )
        if audio_match is None:
            raise DataNotPresent
        audio_url = audio_match.group()
        return [ AudiobookFile(url=audio_url, ext="mp3") ]
