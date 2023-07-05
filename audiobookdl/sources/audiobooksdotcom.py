from .source import Source
from audiobookdl import AudiobookFile, logging, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import NoSourceFound

import re
from typing import List
from urllib.parse import unquote
from urllib3.util import parse_url

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
        book_id = path.split("/")[3]
        scrape_url = f"{BASEURL}{book_id}/1"
        return Audiobook(
            session = self._session,
            metadata = self.get_metadata(scrape_url),
            cover = self.get_cover(scrape_url),
            files = self.get_files(scrape_url),
        )


    def get_metadata(self, scrape_url: str) -> AudiobookMetadata:
        title = self.find_elem_in_page(scrape_url, "h2#bookTitle")
        return AudiobookMetadata(title)


    def get_cover(self, scrape_url: str) -> Cover:
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


    def get_files(self, scrape_url: str) -> List[AudiobookFile]:
        media_url = self.find_in_page(
            scrape_url,
            r"(?<=(mp3: \")).+(?=(&rs))",
            headers = {
                # User agent has to match the one in the cookies
                "User-Agent": self.extract_useragent_from_cookies()
            }
        )
        return [ AudiobookFile(url=media_url, ext="mp3") ]
