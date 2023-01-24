from .source import Source
import re
from urllib.parse import unquote

BASEURL = "https://www.audiobooks.com/book/stream/"


class AudiobooksdotcomSource(Source):
    match = [
        r"{}\d+(/\d)?".format(BASEURL)
    ]
    names = [ "audiobooks.com" ]

    def before(self):
        self.iden = re.search(
                r"(?<=({}))\d+".format(BASEURL),
                self.url).group(0)
        self.scrape_url = f"{BASEURL}{self.iden}/1"

    def get_title(self):
        return self.find_elem_in_page(self.scrape_url, "h2#bookTitle")

    def get_cover(self):
        cover_url = "http:" + self.find_elem_in_page(
                self.scrape_url,
                "img.bookimage",
                data="src")
        return self.get(cover_url)

    def get_user_agent(self):
        raw = self._session.cookies.get("ci_session")
        return unquote(raw).split("\"")[11]

    def get_files(self):
        headers = {
            "User-Agent": self.get_user_agent()
        }
        page: str = self._session.get(
                self.scrape_url,
                headers=headers
                ).content.decode('utf8')
        media_url = re.search(r"(?<=(mp3: \")).+(?=(&rs))", page)
        if media_url is None:
            return []
        files = [{
            "url": media_url.group(0),
            "ext": "mp3"
        }]
        return files
