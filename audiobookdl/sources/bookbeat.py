from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover
from typing import Any, Optional
import uuid
from audiobookdl.exceptions import UserNotAuthorized, MissingBookAccess
import base64
import re


def get_device_id() -> str:
    return (
        str(uuid.uuid3(uuid.NAMESPACE_DNS, "audiobook-dl"))
        + " "
        + base64.b64encode(b"Personal Computer").decode()
    )


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

    def _login(self, username: str, password: str):
        headers = {
            "accept": "application/hal+json",
            "bb-client": "BookBeatApp",
            "bb-device": get_device_id(),
        }
        self._session.headers = headers

        login_json = {"username": username, "password": password}

        tokens = self.post_json(
            "https://api.bookbeat.com/api/login",
            json=login_json
        )
        self._session.headers.update({"authorization": "Bearer " + tokens["token"]})
        self.saved_books = self.get_json(
            "https://api.bookbeat.com/api/my/books/saved?offset=0&limit=100"
        )


    def get_files(self) -> list[AudiobookFile]:
        dl_info = self.get_json(
            "https://api.bookbeat.com/api/downloadinfo/" + str(self.book_info["bookid"])
        )
        # Find license_url
        if "_embedded" in dl_info:
            if "downloads" in dl_info["_embedded"]:
                for dl in dl_info["_embedded"]["downloads"]:
                    if dl["format"] == "audioBook":
                        license_url = dl["_links"]["license"]["href"]
                        break

        if license_url is None:
            raise MissingBookAccess
        lic = self.get_json(license_url)
        self.book_info["license"] = lic
        if "_links" in lic:
            return [
                AudiobookFile(
                    url=lic["_links"]["download"]["href"],
                    headers=self._session.headers,
                    ext="mp4",
                )
            ]
        raise MissingBookAccess


    def get_metadata(self) -> AudiobookMetadata:
        title = self.book_info["metadata"]["title"]
        metadata = AudiobookMetadata(title)
        try:
            contributors = next(
                iter(
                    [
                        e["contributors"]
                        for e in self.book_info["metadata"]["editions"]
                        if e["format"] == "audioBook"
                    ]
                ),
                None,
            )
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

    def get_chapters(self) -> list[Chapter]:
        chapters = []
        for chapter_number, track in enumerate(self.book_info["license"]["tracks"]):
            chapters.append(Chapter(track["start"], f"Chapter {chapter_number+1}"))
        return chapters

    def get_cover(self) -> Cover:
        cover_url = self.book_info["metadata"]["cover"]
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")

    def prepare(self):
        book_id_re = r"(\d+)$"
        wanted_id_match = re.search(book_id_re, self.url)
        if not wanted_id_match:
            raise ValueError(f"Couldn't get bookid from url {self.url}")
        wanted_id = wanted_id_match.group(1)
        for book in self.saved_books["_embedded"]["savedBooks"]:
            if str(book["bookid"]) == wanted_id:
                self.book_info = book
                self.book_info["metadata"] = self._session.get(
                    self.book_info["_links"]["book"]["href"]
                ).json()
                return
        raise MissingBookAccess
