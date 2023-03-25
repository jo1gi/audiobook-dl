from .source import Source
from audiobookdl import AudiobookFile, logging, AudiobookMetadata, Cover
import re
from urllib.parse import unquote
from urllib3.util import parse_url

BASEURL = "https://www.audiobooks.com/book/stream/"


class AudiobooksdotcomSource(Source):
    match = [
        r"{}\d+(/\d)?".format(BASEURL)
    ]
    names = [ "audiobooks.com" ]

    def prepare(self):
        path = parse_url(self.url).path
        book_id = path.split("/")[3] # Third part of path is book id
        logging.debug(f"{book_id=}")
        self.scrape_url = f"{BASEURL}{book_id}/1"


    def get_metadata(self) -> AudiobookMetadata:
        title = self.find_elem_in_page(self.scrape_url, "h2#bookTitle")
        return AudiobookMetadata(title)

    def get_cover(self) -> Cover:
        cover_url = "http:" + \
            self.find_elem_in_page(
                self.scrape_url,
                "img.bookimage",
                data="src"
            )
        return Cover(self.get(cover_url), "jpg")

    def _get_user_agent(self) -> str:
        """Returns user agent from cookies"""
        raw = self._session.cookies.get("ci_session", domain="www.audiobooks.com")
        return unquote(raw).split("\"")[11]

    def get_files(self) -> list[AudiobookFile]:
        # User agent has to match the one in the cookies
        headers = { "User-Agent": self._get_user_agent() }
        media_url = self.find_in_page(
            self.scrape_url,
            r"(?<=(mp3: \")).+(?=(&rs))",
            headers=headers
        )
        return [ AudiobookFile(url=media_url, ext="mp3") ]
