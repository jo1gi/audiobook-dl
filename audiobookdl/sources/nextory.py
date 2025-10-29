from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover, Audiobook, logging
from audiobookdl.exceptions import DataNotPresent, AudiobookDLException
from audiobookdl.utils.image import normalize_cover_image
from typing import Any, Optional, Dict, List
from datetime import datetime
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
                "X-App-Version": "5.47.0",
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

        # Try to get book info directly from API first
        book_info = self.get_book_info_direct(book_id)
        if book_info is None:
            # If direct fetch fails, try adding to want to read list and then fetch
            logging.info("Could not fetch book info directly, attempting to add to want to read list")
            self.add_to_want_to_read(book_id)
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


    def get_book_info_direct(self, book_id: int) -> Optional[dict]:
        """
        Try to fetch book info directly from Nextory API

        :param book_id: Book ID
        :returns: Book metadata or None if not accessible
        """
        try:
            # Try catalog endpoint
            response = self._session.get(
                f"https://api.nextory.com/catalog/v1/products/{book_id}"
            )
            if response.status_code == 200:
                logging.debug("Successfully fetched book info from catalog API")
                return response.json()
        except Exception as e:
            logging.debug(f"Failed to fetch from catalog API: {e}")

        try:
            # Try library endpoint
            response = self._session.get(
                f"https://api.nextory.com/library/v1/products/{book_id}"
            )
            if response.status_code == 200:
                logging.debug("Successfully fetched book info from library API")
                return response.json()
        except Exception as e:
            logging.debug(f"Failed to fetch from library API: {e}")

        return None


    def add_to_want_to_read(self, book_id: int) -> bool:
        """
        Automatically add a book to the want to read list

        :param book_id: Book ID to add
        :returns: True if successful
        """
        try:
            want_to_read_id = self.download_want_to_read_id()
            response = self._session.post(
                f"https://api.nextory.com/library/v1/me/product_lists/{want_to_read_id}/products",
                json={"product_id": book_id}
            )
            if response.status_code in [200, 201]:
                logging.info(f"Successfully added book {book_id} to want to read list")
                return True
            else:
                logging.debug(f"Failed to add to want to read list: {response.status_code}")
                return False
        except Exception as e:
            logging.debug(f"Error adding to want to read list: {e}")
            return False


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
            stream_files = self.get_stream_files(media_url, headers=self._session.headers)
            # Set expected values to suppress debug warnings
            for stream_file in stream_files:
                stream_file.expected_status_code = 200
                stream_file.expected_content_type = "audio/aac"
            files.extend(stream_files)
        return files


    def get_metadata(self, book_info) -> AudiobookMetadata:
        # Debug: Log the full book_info structure to understand available fields
        import json
        logging.debug(f"Nextory book_info keys: {list(book_info.keys())}")
        logging.debug(f"Full book_info: {json.dumps(book_info, indent=2, default=str)}")

        # Required fields
        title = book_info["title"]
        metadata = AudiobookMetadata(title)

        # Authors
        for author in book_info["authors"]:
            metadata.add_author(author["name"])

        # Narrators
        for narrator in book_info["narrators"]:
            metadata.add_narrator(narrator["name"])

        # Description
        if "description_full" in book_info and book_info["description_full"]:
            metadata.description = book_info["description_full"]
        elif "description" in book_info and book_info["description"]:
            metadata.description = book_info["description"]

        # Language - convert language code using pycountry
        if "language" in book_info and book_info["language"]:
            language_code = book_info["language"]
            try:
                # Try alpha_2 code first (e.g., "en", "sv", "no")
                language = pycountry.languages.get(alpha_2=language_code)
                if language is None:
                    # Try alpha_3 code (e.g., "eng", "swe", "nor")
                    language = pycountry.languages.get(alpha_3=language_code)
                if language is not None:
                    metadata.language = language
                else:
                    logging.debug(f"Unknown language code: {language_code}")
            except Exception as e:
                logging.debug(f"Error parsing language code '{language_code}': {e}")

        # Series information - Nextory stores series name in "series" and order in top-level "volume"
        if "series" in book_info and book_info["series"]:
            if isinstance(book_info["series"], dict):
                if "name" in book_info["series"]:
                    metadata.series = book_info["series"]["name"]
            elif isinstance(book_info["series"], str):
                metadata.series = book_info["series"]

        # Series order comes from top-level "volume" field, not from series["vol"]
        if "volume" in book_info and book_info["volume"] is not None:
            metadata.series_order = book_info["volume"]

        # Extract format-specific metadata (ISBN, publisher, publication_date)
        # These fields are nested inside the formats array
        try:
            format_data = self.find_format_data(book_info)

            # ISBN - located in formats array
            if "isbn" in format_data and format_data["isbn"]:
                metadata.isbn = format_data["isbn"]

            # Publisher - located in formats array
            if "publisher" in format_data and format_data["publisher"]:
                if isinstance(format_data["publisher"], dict) and "name" in format_data["publisher"]:
                    metadata.publisher = format_data["publisher"]["name"]
                elif isinstance(format_data["publisher"], str):
                    metadata.publisher = format_data["publisher"]

            # Publication date - located in formats array
            if "publication_date" in format_data and format_data["publication_date"]:
                date_str = format_data["publication_date"]
                try:
                    # Try ISO format first (e.g., "2023-12-15T00:00:00Z")
                    if 'T' in date_str:
                        metadata.release_date = datetime.strptime(
                            date_str.split('.')[0].replace('Z', ''),
                            "%Y-%m-%dT%H:%M:%S"
                        ).date()
                    else:
                        # Try simple date format (e.g., "2023-12-15")
                        metadata.release_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception as e:
                    logging.debug(f"Error parsing publication_date '{date_str}': {e}")
        except DataNotPresent:
            logging.debug("Could not find format data for metadata extraction")

        # Genres/Categories - try multiple possible field structures
        if "genres" in book_info and book_info["genres"]:
            if isinstance(book_info["genres"], list):
                for genre in book_info["genres"]:
                    if isinstance(genre, dict) and "name" in genre:
                        metadata.add_genre(genre["name"])
                    elif isinstance(genre, str):
                        metadata.add_genre(genre)
        elif "categories" in book_info and book_info["categories"]:
            if isinstance(book_info["categories"], list):
                for category in book_info["categories"]:
                    if isinstance(category, dict) and "name" in category:
                        metadata.add_genre(category["name"])
                    elif isinstance(category, str):
                        metadata.add_genre(category)
        elif "category" in book_info and book_info["category"]:
            if isinstance(book_info["category"], dict) and "name" in book_info["category"]:
                metadata.add_genre(book_info["category"]["name"])
            elif isinstance(book_info["category"], str):
                metadata.add_genre(book_info["category"])

        return metadata


    def get_chapters(self, audio_data: dict) -> List[Chapter]:
        # Nextory provides start_at timestamps for individual HLS segments,
        # but these become invalid after combining files with ffmpeg.
        # Return empty list to avoid chapter timing errors.
        # TODO: Calculate chapters based on actual file durations if needed
        return []


    def get_cover(self, book_info) -> Cover:
        cover_url = self.find_format_data(book_info)["img_url"]
        cover_data = self.get(cover_url)
        # Normalize cover image for better compatibility with audiobook apps
        normalized_data, actual_format = normalize_cover_image(cover_data, "jpg")
        return Cover(normalized_data, actual_format)
