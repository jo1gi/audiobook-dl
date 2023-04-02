from .source import Source
from audiobookdl import logging, AudiobookFile, AudiobookMetadata, Chapter, Cover
from audiobookdl.exceptions import NoSourceFound
from audiobookdl.utils.audiobook import AESEncryption
import re

class SaxoSource(Source):
    _authentication_methods = [
        "login"
    ]
    names = [ "Saxo" ]
    match = [
        r"https?://(www.)?saxo.(com|dk)/[^/]+/.+"
    ]
    _APP_OS = "android"
    _APP_VERSION = "6.2.4"

    def _login(self, username: str, password: str) -> None:
        resp = self.post_json(
            "https://auth-read.saxo.com/auth/token",
            data = {
                "username": username,
                "password": password,
                "grant_type": "password",
            },
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        self.bearer_token = resp["access_token"]
        self.user_id = resp["id"]
        logging.debug(f"{self.bearer_token=}")
        logging.debug(f"{self.user_id=}")

    def _get_isbn(self) -> str:
        """Extract isbn of book from url"""
        isbn_match = re.search(f"\d+$", self.url)
        if isbn_match and isbn_match.group():
            return isbn_match.group()
        else:
            raise NoSourceFound

    def _search_for_book(self, isbn: str) -> str:
        """Search for internal book id by isbn number"""
        logging.debug(f"Searching for book with isbn: {isbn}")
        resp = self.get_json(
            f"https://api-read.saxo.com/api/v2/search/user/{self.user_id}/premium/books/{isbn}?booktypefilter=Audiobook",
            headers = {
                "Appauthorization": f"bearer {self.bearer_token}",
                "App-Os": self._APP_OS,
                "App-Version": self._APP_VERSION,
            }
        )
        # Selects the first search result. There should only be one
        book_id = resp["items"][0]["bookId"]
        return book_id

    def _get_book_metadata(self, book_id: str) -> dict:
        """Downloads metadata about book"""
        return self.post_json(
            f"https://api-read.saxo.com/api/v1/book/data/user/{self.user_id}/",
            headers = {
                "Appauthorization": f"bearer {self.bearer_token}",
                "App-Os": self._APP_OS,
                "App-Version": self._APP_VERSION,
            },
            json = [ book_id ]
        )["items"][0]

    def get_files(self) -> list[AudiobookFile]:
        result = []
        for file in self.book_meta["techInfo"]["chapters"]:
            filename = file["fileName"]
            link = self.get_json(
                f"https://api-read.saxo.com/api/v1/book/{self.book_meta['bookId']}/content/encryptedstream/{filename}",
                headers = {
                    "Appauthorization": f"bearer {self.bearer_token}",
                    "App-Os": self._APP_OS,
                    "App-Version": self._APP_VERSION,
                },
            )["link"]
            result.append(AudiobookFile(
                url = link,
                ext = "mp3",
                # Encryption keys extracted from app
                encryption_method = AESEncryption(
                    b"CD3E9D141D8EFC0886912E7A8F3652C4",
                    b"78CB354D377772F1",
                )
            ))
        return result

    def get_metadata(self) -> AudiobookMetadata:
        metadata: dict = self.book_meta["bookMetadata"]
        title = metadata["title"]
        result = AudiobookMetadata(title)
        result.add_authors(metadata["authors"])
        result.add_narrators(metadata["readBy"])
        result.series = metadata.get("seriesName")
        return result

    def get_cover(self) -> Cover:
        cover_url = self.book_meta["bookMetadata"]["image"]["highQualityImageUrl"]
        bytes = self.get(cover_url)
        return Cover(bytes, "jpg")

    def prepare(self) -> None:
        isbn = self._get_isbn()
        book_id = self._search_for_book(isbn)
        logging.debug(f"{book_id=}")
        self.book_meta = self._get_book_metadata(book_id)
