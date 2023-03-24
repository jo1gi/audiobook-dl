from .source import Source
from audiobookdl import  AudiobookFile, logging, utils, AudiobookMetadata, Cover
from audiobookdl.exceptions import UserNotAuthorized, RequestError

from typing import Optional
import re
import json

LOGIN_PAGE_URL = "https://ereolen.dk/adgangsplatformen/login?destination=/user"

class EreolenSource(Source):
    _authentication_methods = [
        "cookies",
        "login"
    ]

    names = [ "eReolen" ]

    login_data = [ "username", "password", "library" ]

    match = [
        r"https?://ereolen.dk/ting/object/.+"
    ]
    book_id: str


    def get_metadata(self) -> AudiobookMetadata:
        title = self.meta["title"]
        metadata = AudiobookMetadata(title)
        metadata.add_author(self.meta["artist"])
        return metadata


    def get_cover(self) -> Cover:
        cover_data = self.get(self.meta["cover"])
        return Cover(cover_data, "jpg")

    def get_files(self) -> list[AudiobookFile]:
        return self.get_stream_files(
            f"https://audio.api.streaming.pubhub.dk/v1/stream/hls/{self.book_id}/playlist.m3u8"
        )

    def _get_libraries(self):
        """Returns list of available libraries for login"""
        libraries_raw = self.find_in_page(
            LOGIN_PAGE_URL,
            "libraries = ({.+})<",
            group_index=1
        )
        libraries = {}
        for library in json.loads(libraries_raw)["folk"]:
            library_name = library["name"]
            library_id = library["branchId"]
            libraries[library_name] = library_id
        return libraries

    def _login(self, username: str, password: str, library: str): # type: ignore
        login_path = self.find_elem_in_page(LOGIN_PAGE_URL, "#borchk-login-form", "action")
        library_attr_name = self.find_elem_in_page(LOGIN_PAGE_URL, "#borchk-login-form label", "for")
        libraries = self._get_libraries()
        logging.debug(f"{login_path=}")
        logging.debug(f"{library_attr_name=}")
        logging.debug(f"{libraries=}")
        if library not in libraries.keys():
            library = utils.nearest_string(library, list(libraries.keys()))
            logging.debug(f"No matching library found. Using nearest: {library}")
        self.post(
            f"https://login.bib.dk{login_path}",
            headers = { "Content-Type": "application/x-www-form-urlencoded" },
            data = {
                library_attr_name: library,
                "agency": libraries[library],
                "userId": username,
                "pincode": password
            }
        )

    def prepare(self):
        ajax: Optional[dict] = self.get_json(f"{self.url}/listen/ajax")
        if not ajax:
            raise RequestError
        logging.debug(f"{ajax=}")
        if ajax[1]["title"] != "Lyt":
            raise UserNotAuthorized
        id_match = re.search(r"(?<=(o=))[0-9a-f\-]+", ajax[1]["data"])
        if id_match and id_match.group():
            self.book_id = id_match.group()
            logging.debug(f"{self.book_id=}")
        else:
            logging.debug("Could not find book id")
            raise UserNotAuthorized
        meta: Optional[dict] = self.get_json(f"https://audio.api.streaming.pubhub.dk/v1/orders/{self.book_id}")
        if meta is None:
            raise UserNotAuthorized
        self.meta = meta
        logging.debug(f"{self.meta=}")
