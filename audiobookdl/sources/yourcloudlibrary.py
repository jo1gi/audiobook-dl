from .source import Source
from audiobookdl import AudiobookFile, logging, AudiobookMetadata, Cover, Audiobook, Chapter
from audiobookdl.exceptions import UserNotAuthorized, RequestError

import requests.utils
import base64
from typing import List
import re

class YourCloudLibrarySource(Source):
    match = [
        r"https?://audio.yourcloudlibrary.com/listen/.+",
        r"https://ebook.yourcloudlibrary.com/library/[^/]+/detail/.+",
    ]
    names = [ "YourCloudLibrary" ]
    login_data = [ "username", "password", "library" ]
    _authentication_methods = [
        "cookies",
        "login"
    ]

    def download(self, url: str) -> Audiobook:
        url = self.get_listening_url(url)
        account_id = self.extract_json_string(url, "accountId")
        logging.debug(f"{account_id=}")
        fulfillment_id = self.extract_json_string(url, "fulfillmentId")
        logging.debug(f"{fulfillment_id=}")
        license_id = self.extract_json_string(url, "licenseId")
        logging.debug(f"{license_id=}")
        session_key = self.extract_json_string(url, "session_key")
        self._session.headers.update({"Session-Key": session_key})
        book_info = self.download_book_info(account_id, fulfillment_id)
        playlist = self.download_playlist(fulfillment_id, license_id)
        return Audiobook(
            session = self._session,
            files = self.get_files(playlist),
            metadata = self.get_metadata(book_info),
            cover = self.download_cover(book_info),
            chapters = self.create_chapters(book_info)
        )


    @staticmethod
    def get_listening_url(url: str) -> str:
        """
        Get url for listening page

        :param url: Url to information or listening page
        :return: Url to listening page
        """
        if re.match(YourCloudLibrarySource.match[0], url):
            return url
        book_id = url.split("/")[-1]
        return f"https://audio.yourcloudlibrary.com/listen/{book_id}"

    def extract_json_string(self, url: str, key: str) -> str:
        """
        Extracts string from json in web page

        :param url: Url of page to extract from
        :param key: Key of value to extract
        :returns: Value
        """
        return self.find_in_page(
            url,
            fr"(?<=(\"{key}\":\"))[^\"]+",
            force_cookies = True,
        )


    @staticmethod
    def get_files(playlist: dict) -> List[AudiobookFile]:
        files = []
        for f in playlist["playlist"]:
            files.append(AudiobookFile(
                url = f["url"],
                ext = "mp3"
            ))
        return files


    @staticmethod
    def get_metadata(book_info: dict) -> AudiobookMetadata:
        metadata = AudiobookMetadata(
            title = book_info["title"],
            authors = book_info["authors"],
            narrators = book_info["narrators"]
        )
        if book_info["series"] is not None and len(book_info["series"]) >= 1:
            metadata.series = book_info["series"][0]
        return metadata


    def download_cover(self, meta) -> Cover:
        cover_url = meta['cover_url']
        cover_data = self.get(f"{cover_url}?aspect=1:1")
        return Cover(cover_data, "jpg")


    @staticmethod
    def create_chapters(book_info: dict) -> List[Chapter]:
        chapters = []
        time = 0
        for chapter in book_info["chapters"]:
            time += chapter["duration"]
            chapters.append(
                Chapter(
                    start = time,
                    title = f"Chapter {chapter['chapter_number']}"
                )
            )
        return chapters

    def download_book_info(self, account_id: str, fulfillment_id: str) -> dict:
        """
        Download metadata about book

        :param url: Book url
        :param fulfillment_id: Id used for book
        :returns: Metadata about book
        """
        return self.get_json(
            f"https://api.findawayworld.com/v4/accounts/{account_id}/audiobooks/{fulfillment_id}",
            force_cookies = True
        )["audiobook"]


    def download_playlist(self, fulfillment_id: str, license_id: str) -> dict:
        """
        Download list of audio files
        """
        license_str = f'{{"license_id":"{license_id}"}}'
        return self.post_json(
            f"https://api.findawayworld.com/v4/audiobooks/{fulfillment_id}/playlists",
            data = license_str
        )


    def _login(self, url: str, username: str, password: str, library: str): # type: ignore
        self.get(f"https://ebook.yourcloudlibrary.com/library/{library}/featured")
        resp = self.post(
            "https://ebook.yourcloudlibrary.com/?_data=root",
            data = {
                "action": "login",
                "barcode": username,
                "pin": password,
                "library": library
            }
        )
