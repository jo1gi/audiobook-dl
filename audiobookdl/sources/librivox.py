from .source import Source
from audiobookdl import AudiobookFile, AudiobookMetadata, Cover, Audiobook
from typing import List


class LibrivoxSource(Source):
    _authentication_methods: List[str] = []

    names = [ "Librivox" ]

    match = [
        r"https?://librivox.org/.+"
    ]
    def download(self, url: str) -> Audiobook:
        return Audiobook(
            session = self._session,
            files = self.get_files(url),
            metadata = self.get_metadata(url),
            cover = self.get_cover(url)
        )


    def get_metadata(self, url: str) -> AudiobookMetadata:
        title = self.find_elem_in_page(url, ".content-wrap h1")
        return AudiobookMetadata(title)

    def get_cover(self, url: str) -> Cover:
        cover_url = self.find_elem_in_page(
            url,
            ".book-page-book-cover img",
            data="src"
        )
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")

    def get_files(self, url: str) -> List[AudiobookFile]:
        parts = self.find_elems_in_page(url, ".chapter-download .chapter-name")
        files = []
        for part in parts:
            files.append(AudiobookFile(
                url = part.get("href"),
                title = part.text,
                ext = "mp3"
            ))
        return files
