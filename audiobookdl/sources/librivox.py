from .source import Source
from audiobookdl import AudiobookFile

from typing import List


class LibrivoxSource(Source):
    _authentication_methods: List[str] = []

    names = [ "Librivox" ]

    match = [
        r"https?://librivox.org/.+"
    ]

    def get_title(self):
        return self.find_elem_in_page(self.url, ".content-wrap h1")

    def get_cover(self):
        return self.get(self.find_elem_in_page(
            self.url,
            ".book-page-book-cover img",
            data="src"))

    def get_files(self) -> List[AudiobookFile]:
        parts = self.find_elems_in_page(self.url,
                                        ".chapter-download .chapter-name")
        files = []
        for part in parts:
            files.append(AudiobookFile(
                url = part.get("href"),
                title = part.text,
                ext = "mp3"
            ))
        return files
