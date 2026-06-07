from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover, Audiobook, BookId, Result, Series, logging
from audiobookdl.exceptions import DataNotPresent, AudiobookDLException, BookHasNoAudiobook, UserNotAuthorized, GenericAudiobookDLException
from typing import Any, Optional, Dict, List, Union

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import hashlib
import uuid
import platform
import pycountry


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

    # Cache for the want-to-read list so we don't refetch it per book
    # when downloading the whole list as a Series.
    _wantlist_cache: Optional[List[dict]] = None


    @staticmethod
    def create_device_id() -> str:
        return str(uuid.uuid3(uuid.NAMESPACE_DNS, "audiobook-dl"))

    def get_compatible_app_version(self):
        d = date.today() - relativedelta(months=2)
        # Nextory ios apps have changed their versioning number to 
        # the format yyyy-mm-dd
        return f"{d.year}-{d.month}-{d.day}"

    def _login(self, url: str, username: str, password: str):
        device_id = self.create_device_id()
        logging.debug(f"{device_id=}")
        self._session.headers.update(
            {
                # New version headers
                "X-Application-Id": self.APP_ID,
                "X-App-Version": self.get_compatible_app_version(),
                "X-Locale": self.LOCALE,
                "X-Model": "Personal Computer",
                "X-Device-Id": device_id,
                "X-Os-Info": "ios"            }
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
        
        
        login_token = session_response_json.get("login_token")
        
        if login_token is None:
            error = session_response_json.get("error", {})
            reason = error.get("key", {})
            error_details = error.get("description", "Unknown Error")    
            if reason == "UserNotFound":
                raise UserNotAuthorized()
            else:
                # 'AppDeprecateError' if "X-App-Version" is incorrect will trigger this
                raise GenericAudiobookDLException(heading=reason, body=error_details)
            
       
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


    def download(self, url) -> Result:
        if self._is_wantlist_url(url):
            return self._download_wantlist()
        book_id = int(url.split("/")[-1].split("-")[-1])
        return self.download_from_id(book_id)


    def download_from_id(self, book_id: int) -> Audiobook:
        book_info = self.find_book_info(book_id, self._get_wantlist())
        logging.debug(f"nextory book_info keys: {sorted(book_info.keys())}")
        audio_data = self.download_audio_data(book_info)
        if "files" not in audio_data:
            logging.debug(f"nextory audio_data without 'files': {audio_data!r}")
            raise BookHasNoAudiobook
        return Audiobook(
            session = self._session,
            files = self.get_files(audio_data),
            metadata = self.get_metadata(book_info),
            cover = self.get_cover(book_info),
            chapters = self.get_chapters(audio_data)
        )


    @staticmethod
    def _is_wantlist_url(url: str) -> bool:
        """Match URLs that refer to the user's want-to-read list rather
        than a specific book, e.g. ``https://nextory.com/se/want-to-read``."""
        return "want-to-read" in url.lower()


    def _get_wantlist(self) -> List[dict]:
        """Return the want-to-read list, fetching it at most once per source."""
        if self._wantlist_cache is None:
            self._wantlist_cache = self.download_want_to_read_list()
        return self._wantlist_cache


    def _download_wantlist(self) -> Series[int]:
        """Build a Series of every audiobook currently on the want-to-read list."""
        books: List[Union[BookId[int], Audiobook]] = []
        for book_info in self._get_wantlist():
            try:
                self.find_format_data(book_info)
            except DataNotPresent:
                # No audio format (ebook-only entry) — skip silently.
                continue
            books.append(BookId(book_info["id"]))
        return Series(
            title = "Nextory want to read",
            books = books,
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
            files.extend(
                self.get_stream_files(
                    file["uri"],
                    headers=self._session.headers,
                    expected_content_type=("audio/aac", "audio/x-aac", "video/MP2T"),
                )
            )
        return files


    def get_metadata(self, book_info) -> AudiobookMetadata:
        series_name, series_order = self._extract_series_metadata(book_info)
        metadata = AudiobookMetadata(
            title = book_info["title"],
            authors = [author["name"] for author in book_info["authors"]],
            narrators = [narrator["name"] for narrator in book_info["narrators"]],
            description = book_info["description_full"],
            series = series_name,
            series_order = series_order,
        )
        # Language sits at the book level as an ISO 639-1 code (e.g. "sv").
        lang_code = book_info.get("language")
        if lang_code:
            language = pycountry.languages.get(alpha_2=lang_code)
            if language is not None:
                metadata.language = language
        # Publisher, ISBN, and publication date live on the audio format.
        try:
            audio_format = self.find_format_data(book_info)
        except DataNotPresent:
            audio_format = None
        if audio_format:
            publisher = audio_format.get("publisher")
            if isinstance(publisher, dict):
                publisher_name = publisher.get("name")
                if publisher_name:
                    metadata.publisher = publisher_name
            isbn = audio_format.get("isbn")
            if isbn:
                metadata.isbn = str(isbn)
            pub_date = audio_format.get("publication_date")
            if pub_date:
                try:
                    metadata.release_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass
        return metadata


    @staticmethod
    def _extract_series_metadata(book_info: dict) -> tuple:
        """Pull series name and position from Nextory's book payload.

        The series object only carries ``name`` and an internal ``vol``
        grouping (always 0 in observed data). The actual position within
        the series lives on the top-level ``volume`` field of the book.
        """
        series = book_info.get("series")
        if not series:
            return None, None
        name = series.get("name")
        position = None
        raw_volume = book_info.get("volume")
        if raw_volume is not None:
            try:
                volume = int(raw_volume)
                if volume > 0:
                    position = volume
            except (TypeError, ValueError):
                pass
        return name, position


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
