from ..utils.service import Service
import re, requests

BASEURL = "https://www.audiobooks.com/book/stream/"

class AudiobooksdotcomService(Service):
    require_cookies = True
    match = [
        r"{}\d+(/\d)?".format(BASEURL)
    ]

    def before(self):
        self.iden = re.search(r"(?<=({}))\d+".format(BASEURL), self.url).group(0)
        self.scrape_url = f"{BASEURL}{self.iden}/1"

    def get_title(self):
        return self.find_elem_in_page(self.scrape_url, "h2#bookTitle")

    def get_cover(self):
        cover_url = "http:" + self.find_elem_in_page(self.scrape_url, "img.bookimage", data="src")
        return self.get(cover_url)

    def get_files(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0",
        }
        page = self._session.get(self.scrape_url, headers=headers).content.decode('utf8')
        media_url = re.search(r"(?<=(mp3: \")).+(?=(&rs))", page)
        if media_url == None:
            return []
        files = [{
            "url": media_url.group(0),
            "ext": "mp3"
        }]
        return files
