from .source import Source
from audiobookdl import AudiobookFile, AudiobookMetadata, Cover
from typing import List


class LibrivoxSource(Source):
    _authentication_methods: List[str] = []

    names = [ "Librivox" ]

    match = [
        r"https?://librivox.org/.+"
    ]


    def get_metadata(self) -> AudiobookMetadata:
        title = self.find_elem_in_page(self.url, ".content-wrap h1")
        return AudiobookMetadata(title)

    def get_cover(self) -> Cover:
        cover_url = self.find_elem_in_page(
            self.url,
            ".book-page-book-cover img",
            data="src"
        )
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")

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
