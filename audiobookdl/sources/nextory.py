from .source import Source
from audiobookdl import AudiobookFile, Chapter, AudiobookMetadata, Cover
from typing import Any, Optional
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
        r"https?://(www.)?nextory.+",
    ]
    names = [ "Nextory" ]
    _authentication_methods = [
        "login",
    ]

    user_data: dict
    book_info: dict

    def get_salt(self) -> str:
        url = "https://api.nextory.se/api/app/catalogue/7.5/salt"
        resp = self._session.get(url)
        if resp.status_code != 200:
            raise RuntimeError("Couldn't get salt from nextory.")
        return resp.json()["data"]["salt"]

    def _login(self, username: str, password: str):
        # Step one
        login_url = "https://api.nextory.se/api/app/user/7.5/login"
        headers = {
            "appid": "200",
            "model": "Personal Computer",
            "locale": "en_GB",
            "deviceid": get_device_id(),
            "osinfo": platform.platform(),
            "version": "4.34.6",
            #"user-agent": "okhttp/4.9.3",
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
        params = {
            "loginkey": account_list["data"]["accounts"][0]["loginkey"],
            "checksum": calculate_password_checksum(account_list["data"]["accounts"][0]["loginkey"], salt)
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


    def get_files(self) -> list[AudiobookFile]:
        return [AudiobookFile(url=self.book_info["file"]["url"], headers=self._session.headers, ext="mp3")]

    def get_metadata(self) -> AudiobookMetadata:
        title = self.book_info["title"]
        metadata = AudiobookMetadata(title)
        try:
            book_info = self._session.get("https://api.nextory.se/api/app/product/7.5/bookinfo",
                                         params={"id": self.book_info["id"]}).json()
            metadata.add_authors(self.book_info["authors"])
            metadata.add_narrators(book_info["data"]["books"]["narrators"])
            return metadata
        except:
            return metadata

    def get_chapters(self) -> list[Chapter]:
        # Nextory has no chapters...?
        return []

    def get_cover(self) -> Cover:
        cover_url = self.book_info["imgurl"].replace("{$width}", "640")
        cover_data = self.get(cover_url)
        return Cover(cover_data, "jpg")

    def prepare(self):
        wanted_id = self.url.split("-")[-1].replace("/", "")
        for book in self.user_data["active"]["data"]["books"]:
            if str(book["id"]) == wanted_id:
                self.book_info = book
                return
        raise PermissionError(f"Book with id {wanted_id} was not found in My Library.")
