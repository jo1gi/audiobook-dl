from .source import Source
from audiobookdl import Audiobook, AudiobookFile, AudiobookMetadata, Cover
from typing import List

class BlinkistSource(Source):
    names = [ "Blinkist" ]
    _authentication_methods = [ "cookies" ]
    match = [
        r"https://www.blinkist.com/en/nc/reader/.+"
    ]

    def download(self, url: str) -> Audiobook:
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "x-requested-with": "XMLHttpRequest"
        })
        book_id = self.extract_id_from_url(url)
        book_info = self.download_book_info(book_id)
        return Audiobook(
            session = self._session,
            files = self.download_files(book_info),
            metadata = self.format_metadata(book_info),
            cover = self.download_cover(book_info)
        )


    def download_cover(self, book_info: dict) -> Cover:
        cover_url = book_info["book"]["cover"]["default"]["src"]
        cover_data = self._session.get(cover_url).content
        return Cover(cover_data, "jpg")


    @staticmethod
    def format_metadata(book_info: dict) -> AudiobookMetadata:
        return AudiobookMetadata(
            title = book_info["book"]["title"],
            authors = [ book_info["book"]["author"] ]
        )


    def download_files(self, book_info: dict) -> List[AudiobookFile]:
        files = []
        book_id = book_info["book"]["id"]
        for chapter in book_info["chapters"]:
            chapter_id = chapter["id"]
            audio_url = self._session.get(
                f"https://www.blinkist.com/api/books/{book_id}/chapters/{chapter_id}"
            ).json()["signed_audio_url"]
            files.append(AudiobookFile(
                url = audio_url,
                ext = "m4a",
            ))
        return files


    def download_book_info(self, book_id: str) -> dict:
        return self._session.get(
            f"https://www.blinkist.com/api/books/{book_id}/chapters",
        ).json()


    @staticmethod
    def extract_id_from_url(url: str) -> str:
        last = url.split("/")[-1]
        without_params = last.split("?")[0]
        return without_params
