from ..utils.service import Service
import re

BASEURL = "https://www.audiobooks.com/book/stream/"

class AudiobooksdotcomService(Service):
    require_cookies = True
    match = [
        r"{}\d+(/\d)?".format(BASEURL)
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        # Setup variables thats used in multiple places
        self.iden = re.search(r"(?<=({}))\d+".format(BASEURL), url).group(0)
        self.scrape_url = f"{BASEURL}{self.iden}/1"

    def get_title(self):
        return self.find_elem_in_page(self.scrape_url, "h2#bookTitle")

    def get_files(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0"
        }
        media_url = self.find_in_page(self.scrape_url, r"(?<=(mp3: \")).+(?=(&rs))", headers=headers)
        files = [{
            "url": media_url,
            "ext": "mp3"
        }]
        return files
