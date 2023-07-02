from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover, Audiobook
from audiobookdl.exceptions import DataNotPresent
from typing import Any, Optional, Dict
import hashlib
import uuid
import platform


def calculate_checksum(username: str, password: str, salt: str) -> str:
    return get_checksum(username + salt + password)


def calculate_password_checksum(password: str, salt: str) -> str:
    return get_checksum(password + salt)


def get_checksum(s: str) -> str:
    return hashlib.md5(s.encode()).digest().hex().zfill(32).upper()


def get_device_id() -> str:
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, "audiobook-dl"))


class NextorySource(Source):
    match = [
        r"https?://((www|catalog-\w\w).)?nextory.+",
    ]
    names = [ "Nextory" ]
    _authentication_methods = [
        "login",
    ]

    user_data: dict
    book_info: dict

    def download(self, url) -> Audiobook:
        book_id = url.split("-")[-1].replace("/", "")
        book_info = self.find_book_info(book_id)
        return Audiobook(
            session = self._session,
            files = self.get_files(book_info),
            metadata = self.get_metadata(book_info),
            cover = self.get_cover(book_info),
        )


    def find_book_info(self, book_id: str) -> Dict:
        """
        Find metadata about book in list of active books

        :param book_id: Book id
        :returns: Book metadata
        """
        for book in self.user_data["active"]["data"]["books"]:
            if str(book["id"]) == book_id:
                return book
        raise DataNotPresent


    def get_salt(self) -> str:
        url = "https://api.nextory.se/api/app/catalogue/7.5/salt"
        resp = self._session.get(url)
        if resp.status_code != 200:
            raise RuntimeError("Couldn't get salt from nextory.")
        return resp.json()["data"]["salt"]


    def _login(self, url: str, username: str, password: str):
        # Step one
        login_url = "https://api.nextory.se/api/app/user/7.5/login"
        headers = {
            "appid": "200",
            "model": "Personal Computer",
            "locale": "en_GB",
            "deviceid": get_device_id(),
            "osinfo": platform.platform(),
            "version": "4.34.6",
        }

        self._session.headers = headers
        salt = self.get_salt()
        files = {
            "username": (None, username),
            "password": (None, password),
            "checksum": (None, calculate_checksum(username, password, salt)),
        }
        resp = self._session.post(login_url, files=files)
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step one")

        login_info = resp.json()
        self._session.headers.update({'token': login_info["data"]["token"]})

        # Step two
        resp = self._session.get("https://api.nextory.se/api/app/user/7.5/accounts/list")
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step two")
        account_list = resp.json()

        # Step three
        login_key = account_list["data"]["accounts"][0]["loginkey"]
        params = {
            "loginkey": login_key,
            "checksum": calculate_password_checksum(login_key, salt)
        }

        resp = self._session.get(login_url, params=params)
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step three")

        account_info = resp.json()
        self._session.headers.update({'token': account_info["data"]["token"]})
        self._session.headers.update({'canary': account_info["data"]["canary"]})

        # Step four
        resp = self._session.get("https://api.nextory.se/api/app/library/7.5/active")
        if resp.status_code != 200:
            raise PermissionError("Error in NextorySource login step four")

        active = resp.json()

        self.user_data = {
            "login_info": login_info,
            "account_list": account_list,
            "account_info": account_info,
            "active": active,
        }
        self._session.headers.update({'apiver': "7.5"})


    def get_files(self, book_info) -> list[AudiobookFile]:
        return [
            AudiobookFile(
                url=book_info["file"]["url"],
                headers=self._session.headers,
                ext="mp3"
            )
        ]


    def get_metadata(self, book_info) -> AudiobookMetadata:
        title = book_info["title"]
        metadata = AudiobookMetadata(title)
        try:
            metadata.add_authors(self.book_info["authors"])
            narrators = self._session.get(
                "https://api.nextory.se/api/app/product/7.5/bookinfo",
                params={"id": self.book_info["id"]}
            ).json()["data"]["books"]["narrators"]
            metadata.add_narrators(narrators)
            return metadata
        except:
            return metadata

    def get_chapters(self) -> list[Chapter]:
        # Nextory has no chapters...?
        return []


    def get_cover(self, book_info) -> Cover:
        cover_url = book_info["imgurl"].replace("{$width}", "640")
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")
