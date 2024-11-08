from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover, Audiobook, logging
from audiobookdl.exceptions import DataNotPresent, AudiobookDLException
from typing import Any, Optional, Dict, List
import hashlib
import uuid
import platform


def calculate_checksum(username: str, password: str, salt: str) -> str:
    return get_checksum(username + salt + password)


def calculate_password_checksum(password: str, salt: str) -> str:
    return get_checksum(password + salt)


def get_checksum(s: str) -> str:
    return hashlib.md5(s.encode()).digest().hex().zfill(32).upper()



class NextorySource(Source):
    match = [
        r"https?://((www|catalog-\w\w).)?nextory.+",
    ]
    names = [ "Nextory" ]
    _authentication_methods = [
        "login",
    ]
    APP_ID = "200"
    LOCALE = "en_GB"


    @staticmethod
    def create_device_id() -> str:
        return str(uuid.uuid3(uuid.NAMESPACE_DNS, "audiobook-dl"))


    def _login(self, url: str, username: str, password: str):
        device_id = self.create_device_id()
        logging.debug(f"{device_id=}")
        self._session.headers.update(
            {
                # New version headers
                "X-Application-Id": self.APP_ID,
                "X-App-Version": "5.4.1",
                "X-Locale": self.LOCALE,
                "X-Model": "Personal Computer",
                "X-Device-Id": device_id,
		"X-Os-Info": "Android"
            }
        )
        # Login for account
        session_response = self._session.post(
            "https://api.nextory.com/user/v1/sessions",
            json = {
                "identifier": username,
                "password": password
            },
        )
        session_response_json = session_response.json()
        logging.debug(f"{session_response=}")
        login_token = session_response_json["login_token"]
        country = session_response_json["country"]
        self._session.headers.update(
            {
                "token": login_token,
                "X-Login-Token": login_token,
                "X-Country-Code": country,
            }
        )
        # Login for user
        profiles_response = self._session.get(
            "https://api.nextory.com/user/v1/me/profiles",
        )
        profiles_response_json = profiles_response.json()
        profile = profiles_response_json["profiles"][0]
        login_key = profile["login_key"]
        authorize_response = self._session.post(
            "https://api.nextory.com/user/v1/profile/authorize",
            json = {
                "login_key": login_key
            }
        )
        authorize_response_json = authorize_response.json()
        profile_token = authorize_response_json["profile_token"]
        self._session.headers.update({"X-Profile-Token": profile_token})
        logging.debug(f"{profile_token=}")


    def download(self, url) -> Audiobook:
        book_id = int(url.split("/")[-1].split("-")[-1])
        want_to_read_list = self.download_want_to_read_list()
        book_info = self.find_book_info(book_id, want_to_read_list)
        audio_data = self.download_audio_data(book_info)
        return Audiobook(
            session = self._session,
            files = self.get_files(audio_data),
            metadata = self.get_metadata(book_info),
            cover = self.get_cover(book_info),
            chapters = self.get_chapters(audio_data)
        )


    def find_book_info(self, book_id: int, want_to_read_list: list) -> dict:
        """
        Find metadata about book in list of active books

        :param format_id: Id of audio format
        :param want_to_read_list: List of books the user want to read
        :returns: Book metadata
        """
        for book in want_to_read_list:
            if book["id"] == book_id:
                return book
        raise AudiobookDLException(error_description = "nextory_want_to_read")


    def download_want_to_read_id(self) -> str:
        """Downloads profile id for want to read list"""
        products_lists = self._session.get(
            "https://api.nextory.com/library/v1/me/product_lists",
            params = {
                "page": 0,
                "per": 50
            }
        ).json()["product_lists"]
        for product_list in products_lists:
            if product_list["type"] == "want_to_read":
                return product_list["id"]
        raise DataNotPresent


    def download_want_to_read_list(self) -> List[dict]:
        want_to_read_id = self.download_want_to_read_id()
        return self._session.get(
            "https://api.nextory.com/library/v1/me/product_lists/want_to_read/products",
            params = {
                "page": "0",
                "per": "1000",
                "id": want_to_read_id
            }
        ).json()["products"]


    def download_audio_data(self, book_info: dict) -> dict:
        format_data = self.find_format_data(book_info)
        format_id = format_data["identifier"]
        return self._session.get(
            f"https://api.nextory.com/reader/books/{format_id}/packages/audio"
        ).json()


    @staticmethod
    def find_format_data(book_info: dict) -> dict:
        for format in book_info["formats"]:
            if format["type"] == "hls":
                return format
        raise DataNotPresent


    def get_files(self, audio_data) -> List[AudiobookFile]:
        files = []
        for file in audio_data["files"]:
            # master url redirects to media url
            # TODO Handle redirect correctly
            media_url = file["uri"].replace("master", "media")
            files.extend(
                self.get_stream_files(media_url, headers=self._session.headers)
            )
        return files


    def get_metadata(self, book_info) -> AudiobookMetadata:
        return AudiobookMetadata(
            title = book_info["title"],
            authors = [author["name"] for author in book_info["authors"]],
            narrators = [narrator["name"] for narrator in book_info["narrators"]],
            description = book_info["description_full"]
        )


    def get_chapters(self, audio_data: dict) -> List[Chapter]:
        chapters = []
        for index, file in enumerate(audio_data["files"]):
            chapters.append(
                Chapter(title = f"Chapter {index+1}", start = file["start_at"])
            )
        return chapters


    def get_cover(self, book_info) -> Cover:
        cover_url = self.find_format_data(book_info)["img_url"]
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")
