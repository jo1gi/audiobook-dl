from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover, Audiobook
from typing import Any, List, Optional, Dict
import uuid
from audiobookdl.exceptions import UserNotAuthorized, MissingBookAccess
import base64
import re




class BookBeatSource(Source):
    match = [
        r"https?://(www.)?bookbeat.+",
    ]
    names = ["BookBeat"]
    _authentication_methods = [
        "login",
    ]
    saved_books: dict
    book_info: dict

    @staticmethod
    def create_device_id() -> str:
        """Create random device id"""
        return (
            str(uuid.uuid3(uuid.NAMESPACE_DNS, "audiobook-dl"))
            + " "
            + base64.b64encode(b"Personal Computer").decode()
        )

    def _login(self, url: str, username: str, password: str):
        headers = {
            "accept": "application/hal+json",
            "bb-client": "BookBeatApp",
            "bb-device": self.create_device_id(),
        }
        self._session.headers = headers
        login_json = {"username": username, "password": password}
        tokens = self.post_json(
            "https://api.bookbeat.com/api/login",
            json=login_json
        )
        token = tokens["token"]
        self._session.headers.update({"authorization": f"Bearer {token}"})
        self.saved_books = self.get_json(
            "https://api.bookbeat.com/api/my/books/saved?offset=0&limit=100"
        )


    def download(self, url: str) -> Audiobook:
        book_id_re = r"(\d+)$"
        wanted_id_match = re.search(book_id_re, url)
        if not wanted_id_match:
            raise ValueError(f"Couldn't get bookid from url {url}")
        wanted_id = wanted_id_match.group(1)
        book_info = self.find_book_info(wanted_id)
        return Audiobook(
            session = self._session,
            files = self.get_files(book_info),
            metadata = self.get_metadata(book_info),
            cover = self.get_cover(book_info),
            chapters = self.get_chapters(book_info),
        )


    def download_license_url(self, book_info):
        dl_info = self.get_json(
            "https://api.bookbeat.com/api/downloadinfo/" + str(book_info["bookid"])
        )
        if "_embedded" in dl_info:
            if "downloads" in dl_info["_embedded"]:
                for dl in dl_info["_embedded"]["downloads"]:
                    if dl["format"] == "audioBook":
                        return dl["_links"]["license"]["href"]
        raise MissingBookAccess


    def get_files(self, book_info: Dict) -> List[AudiobookFile]:
        license_url = self.download_license_url(book_info)
        lic = self.get_json(license_url)
        book_info["license"] = lic
        if "_links" in lic:
            return [
                AudiobookFile(
                    url=lic["_links"]["download"]["href"],
                    headers=self._session.headers,
                    ext="mp4",
                )
            ]
        raise MissingBookAccess


    def get_metadata(self, book_info: Dict) -> AudiobookMetadata:
        title = book_info["metadata"]["title"]
        metadata = AudiobookMetadata(title)
        try:
            contributors = [
                e["contributors"] for e in book_info["metadata"]["editions"] if e["format"] == "audioBook"
            ][0]
            if not contributors:
                return metadata
            for contributor in contributors:
                name = f"{contributor['firstname']} {contributor['lastname']}"
                if "author" in contributor["role"]:
                    metadata.add_author(name)
                if "narrator" in contributor["role"]:
                    metadata.add_narrator(name)
            return metadata
        except:
            return metadata


    @staticmethod
    def get_chapters(book_info: Dict) -> List[Chapter]:
        chapters = []
        for chapter_number, track in enumerate(book_info["license"]["tracks"]):
            chapters.append(Chapter(track["start"], f"Chapter {chapter_number+1}"))
        return chapters


    def get_cover(self, book_info: Dict) -> Cover:
        cover_url = book_info["metadata"]["cover"]
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")


    def find_book_info(self, book_id: str) -> Dict:
        """Find book by id from owned books"""
        for book in self.saved_books["_embedded"]["savedBooks"]:
            if str(book["bookid"]) == book_id:
                book["metadata"] = self._session.get(
                    book["_links"]["book"]["href"]
                ).json()
                return book
        raise MissingBookAccess
